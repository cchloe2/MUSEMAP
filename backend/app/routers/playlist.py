import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.auth_utils import get_token
from app.services import mood_engine, spotify_client
from app.models.schemas import GeneratePlaylistRequest

# ── Logger structuré (visible dans le terminal uvicorn) ──
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("musemap.playlist")

router = APIRouter(prefix="/playlist", tags=["playlist"])


@router.post("/generate")
async def generate_playlist(
    request: GeneratePlaylistRequest,
    token: str = Depends(get_token),
):
    """Génère une playlist depuis un prompt sans la sauvegarder."""
    try:
        result = await mood_engine.generate_playlist(
            access_token=token,
            prompt=request.prompt,
            genres=request.genres,
            mood=request.mood,
            track_count=request.track_count,
        )
        return result
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.post("/save")
async def save_playlist(
    request: GeneratePlaylistRequest,
    playlist_name: str = Query(default="MuseMap Playlist"),
    token: str = Depends(get_token),
):
    """Génère ET sauvegarde la playlist sur Spotify."""

    # ════════════════════════════════════════
    # ÉTAPE 1 — Récupération du user_id
    # ════════════════════════════════════════
    logger.info("▶ [SAVE] Étape 1 : récupération du profil utilisateur...")

    async with httpx.AsyncClient() as client:
        me_response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    logger.info(f"   /me status code : {me_response.status_code}")
    logger.info(f"   /me body        : {me_response.text[:300]}")

    if me_response.status_code != 200:
        raise HTTPException(
            status_code=me_response.status_code,
            detail=f"/me a échoué : {me_response.text}"
        )

    me_data = me_response.json()
    user_id = me_data.get("id", "").strip()

    logger.info(f"   user_id extrait : '{user_id}'")

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="user_id vide — le token ne permet pas de lire le profil. "
                   "Reconnecte-toi via /auth/login."
        )

    # ════════════════════════════════════════
    # ÉTAPE 2 — Génération des tracks
    # ════════════════════════════════════════
    logger.info("▶ [SAVE] Étape 2 : génération des tracks via mood engine...")

    result = await mood_engine.generate_playlist(
        access_token=token,
        prompt=request.prompt,
        genres=request.genres,
        mood=request.mood,
        track_count=request.track_count,
    )
    tracks = result["tracks"]

    logger.info(f"   tracks générés  : {len(tracks)}")

    if not tracks:
        raise HTTPException(
            status_code=404,
            detail="Aucun track trouvé — essaie d'autres genres ou un prompt différent."
        )

    # ── Validation + formatage des URIs ──
    uris = []
    for t in tracks:
        raw_id = t.spotify_id.strip()

        # Nettoie au cas où l'ID contiendrait déjà le préfixe
        if raw_id.startswith("spotify:track:"):
            uri = raw_id
        elif raw_id.startswith("spotify:"):
            # ex: "spotify:album:xxx" — anomalie à logger
            logger.warning(f"   ⚠️  ID inattendu ignoré : '{raw_id}'")
            continue
        else:
            uri = f"spotify:track:{raw_id}"

        # Vérifie que l'ID a bien la longueur standard Spotify (22 chars)
        track_id = uri.replace("spotify:track:", "")
        if len(track_id) != 22:
            logger.warning(f"   ⚠️  ID longueur anormale ({len(track_id)}) : '{track_id}'")

        uris.append(uri)

    logger.info(f"   URIs valides    : {len(uris)}")
    logger.info(f"   Exemple URI[0]  : {uris[0] if uris else 'AUCUN'}")

    if not uris:
        raise HTTPException(
            status_code=422,
            detail="Aucun URI Spotify valide après validation."
        )

    # ════════════════════════════════════════
    # ÉTAPE 3 — Création de la playlist
    # ════════════════════════════════════════
    logger.info(f"▶ [SAVE] Étape 3 : création de la playlist pour user '{user_id}'...")

    description = f"Générée par MuseMap · {request.prompt[:80]}"

    try:
        playlist = await spotify_client.create_playlist(
            token,
            user_id,
            name=playlist_name,
            description=description,
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"   ❌ create_playlist échoué : {e.response.status_code} — {e.response.text}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Création playlist échouée : {e.response.text}"
        )

    playlist_id = playlist.get("id", "")
    playlist_url = playlist.get("external_urls", {}).get("spotify", "")

    logger.info(f"   playlist_id     : '{playlist_id}'")
    logger.info(f"   playlist_url    : '{playlist_url}'")

    if not playlist_id:
        raise HTTPException(
            status_code=500,
            detail=f"Spotify n'a pas retourné d'ID de playlist. Réponse : {playlist}"
        )

    # ════════════════════════════════════════
    # ÉTAPE 4 — Ajout des tracks
    # ════════════════════════════════════════
    logger.info(f"▶ [SAVE] Étape 4 : ajout de {len(uris)} tracks à '{playlist_id}'...")

    # Spotify accepte max 100 URIs par requête — on chunk par sécurité
    chunk_size = 100
    for i in range(0, len(uris), chunk_size):
        chunk = uris[i:i + chunk_size]
        logger.info(f"   chunk [{i}:{i+len(chunk)}] → {len(chunk)} tracks")
        try:
            await spotify_client.add_tracks_to_playlist(token, playlist_id, chunk)
        except httpx.HTTPStatusError as e:
            logger.error(f"   ❌ add_tracks échoué : {e.response.status_code} — {e.response.text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ajout des tracks échoué : {e.response.text}"
            )

    logger.info("✅ [SAVE] Playlist sauvegardée avec succès !")

    return {
        "message": "Playlist créée sur Spotify ✅",
        "playlist_id": playlist_id,
        "playlist_url": playlist_url,
        "track_count": len(uris),
        "interpretation": result["interpretation"],
        "debug": {
            "user_id": user_id,
            "uris_sample": uris[:3],
        },
    }
