"""
Studio Router — Hub de gestion musicale cross-plateforme.
Filtre des playlists existantes et exporte le résultat.
"""

import asyncio
import io
import csv
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from app.services.auth_utils import get_token
from app.services.spotify_client import spotify
from app.models.schemas import StudioFilterRequest, ExportToSpotifyRequest, TrackResponse

logger = logging.getLogger("musemap.studio")
router = APIRouter(prefix="/studio", tags=["studio"])


# ════════════════════════════════════════════════════════
#  FILTRAGE — cœur du Studio
# ════════════════════════════════════════════════════════

@router.post("/filter")
async def filter_tracks(
    request: StudioFilterRequest,
    token: str = Depends(get_token),
):
    """
    Récupère les tracks de plusieurs playlists et applique des filtres.
    Retourne la liste filtrée + les stats de filtrage.
    """
    if not request.playlist_ids:
        raise HTTPException(status_code=400, detail="Fournis au moins un playlist_id.")

    # ── Fetch parallèle de toutes les playlists ──
    logger.info(f"▶ [STUDIO] Fetch de {len(request.playlist_ids)} playlists...")
    tasks = [
        spotify.get_playlist_tracks(token, pid)
        for pid in request.playlist_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # ── Agrégation + déduplication ──
    all_tracks: list[TrackResponse] = []
    seen_ids: set[str] = set()
    for batch in results:
        if isinstance(batch, Exception):
            logger.warning(f"   Erreur sur une playlist : {batch}")
            continue
        for track in batch:
            if track.spotify_id not in seen_ids:
                seen_ids.add(track.spotify_id)
                all_tracks.append(track)

    logger.info(f"   Total avant filtrage : {len(all_tracks)} tracks")

    # ── Application des filtres ──
    filtered = all_tracks

    if request.genres:
        genres_lower = [g.lower() for g in request.genres]
        filtered = [
            t for t in filtered
            if any(g in (t.artist.lower() + " " + (t.album or "").lower()) for g in genres_lower)
            or any(g in [tg.lower() for tg in (t.genres or [])] for g in genres_lower)
        ]

    if request.year_min is not None:
        filtered = [t for t in filtered if t.release_year and t.release_year >= request.year_min]

    if request.year_max is not None:
        filtered = [t for t in filtered if t.release_year and t.release_year <= request.year_max]

    if request.popularity_min is not None:
        filtered = [t for t in filtered if t.popularity and t.popularity >= request.popularity_min]

    if request.popularity_max is not None:
        filtered = [t for t in filtered if t.popularity and t.popularity <= request.popularity_max]

    logger.info(f"   Après filtrage : {len(filtered)} tracks")

    return {
        "tracks": filtered,
        "stats": {
            "total_before_filter": len(all_tracks),
            "total_after_filter": len(filtered),
            "playlists_merged": len(request.playlist_ids),
            "filters_applied": {
                "genres": request.genres,
                "year_min": request.year_min,
                "year_max": request.year_max,
                "popularity_min": request.popularity_min,
                "popularity_max": request.popularity_max,
            },
        },
    }


# ════════════════════════════════════════════════════════
#  EXPORT SPOTIFY
# ════════════════════════════════════════════════════════

@router.post("/export/spotify")
async def export_to_spotify(
    request: ExportToSpotifyRequest,
    token: str = Depends(get_token),
):
    """
    Crée une playlist Spotify privée avec les tracks sélectionnés.
    Payload : liste d'IDs bruts + nom + public (false par défaut).
    """
    if not request.track_ids:
        raise HTTPException(status_code=400, detail="Aucun track_id fourni.")

    # Récupère user_id
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    user_id = r.json().get("id", "").strip()

    # Crée la playlist (privée par défaut)
    try:
        playlist = await spotify.create_playlist(
            token, user_id,
            name=request.playlist_name,
            description="Exporté depuis MuseMap Studio",
            public=request.public,     # False par défaut ✅
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code,
                            detail=f"Création playlist échouée : {e.response.text}")

    playlist_id = playlist.get("id", "")
    if not playlist_id:
        raise HTTPException(status_code=500, detail="Spotify n'a pas retourné d'ID.")

    # Ajoute les tracks (chunks de 100)
    for i in range(0, len(request.track_ids), 100):
        chunk = request.track_ids[i:i + 100]
        try:
            await spotify.add_tracks_to_playlist(token, playlist_id, chunk)
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code,
                                detail=f"Ajout tracks échoué : {e.response.text}")

    return {
        "message": "Playlist exportée sur Spotify ✅",
        "playlist_id": playlist_id,
        "playlist_url": playlist.get("external_urls", {}).get("spotify"),
        "track_count": len(request.track_ids),
        "public": request.public,
    }


# ════════════════════════════════════════════════════════
#  EXPORT CSV — universel, infaillible
# ════════════════════════════════════════════════════════

@router.post("/export/csv")
async def export_to_csv(
    tracks: list[TrackResponse],
):
    """
    Génère un fichier CSV téléchargeable.
    Colonnes : Titre, Artiste, Album, Année, Popularité, ISRC, URL Spotify.
    Ne nécessite pas de token — les données sont déjà côté front.
    """
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_ALL)

    # Header
    writer.writerow([
        "Titre", "Artiste", "Album",
        "Année", "Popularité", "ISRC",
        "URL Spotify"
    ])

    for t in tracks:
        writer.writerow([
            t.name,
            t.artist,
            t.album or "",
            t.release_year or "",
            t.popularity or "",
            t.isrc or "",
            t.spotify_url or "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=musemap_export.csv"},
    )
