"""
Mood Engine — Orchestre l'ensemble du pipeline de génération.

Pipeline :
  1. LLM interprète le prompt → paramètres musicaux
  2. Spotify Search multi-requêtes parallèles
  3. Scoring par popularité + déduplication
  4. Sélection finale des N meilleurs tracks
"""

import asyncio
import random
from app.services import llm_service, spotify_client
from app.models.schemas import TrackResponse


async def generate_playlist(
    access_token: str,
    prompt: str,
    genres: list[str],
    mood: str,
    track_count: int = 20,
) -> dict:
    """
    Point d'entrée principal du moteur.
    Retourne un dict avec les tracks et les métadonnées de génération.
    """

    # ── Étape 1 : Interprétation LLM ──────────────────────
    interpretation = await llm_service.interpret_prompt(prompt, genres, mood)

    effective_genres  = interpretation.get("genres") or genres
    mood_keywords     = interpretation.get("mood_keywords", [])
    artist_hints      = interpretation.get("artists_hints", [])
    energy            = interpretation.get("energy", "medium")

    # ── Étape 2 : Recherches Spotify parallèles ────────────
    # On lance plusieurs recherches en même temps pour plus de diversité
    search_tasks = []

    # Par genre + mood keywords
    mood_str = " ".join(mood_keywords[:3])
    for genre in effective_genres[:3]:  # max 3 genres simultanés
        search_tasks.append(
            spotify_client.search_tracks_by_genre(
                access_token,
                genre=genre,
                mood_keywords=mood_str,
                limit=15,
            )
        )

    # Par artistes suggérés par le LLM
    for artist in artist_hints[:2]:
        search_tasks.append(
            spotify_client.search_tracks_by_artist(
                access_token,
                artist=artist,
                limit=8,
            )
        )

    # Exécution parallèle de toutes les recherches
    results = await asyncio.gather(*search_tasks, return_exceptions=True)

    # ── Étape 3 : Agrégation + scoring ─────────────────────
    all_tracks: list[TrackResponse] = []
    seen_ids: set[str] = set()

    for batch in results:
        if isinstance(batch, Exception):
            continue  # on ignore les erreurs silencieusement
        for track in batch:
            if track.spotify_id not in seen_ids:
                seen_ids.add(track.spotify_id)
                all_tracks.append(track)

    # ── Étape 4 : Scoring par popularité + énergie ─────────
    def score_track(track: TrackResponse) -> float:
        base = track.popularity or 50

        # Bonus énergie : on favorise les tracks populaires
        # selon l'énergie demandée
        if energy == "high":
            bonus = base * 0.3 if base > 70 else 0
        elif energy == "low":
            bonus = base * 0.3 if base < 60 else 0
        else:
            bonus = 0

        # Légère randomisation pour éviter des playlists identiques
        noise = random.uniform(-5, 5)
        return base + bonus + noise

    scored = sorted(all_tracks, key=score_track, reverse=True)

    # ── Étape 5 : Sélection finale ─────────────────────────
    final_tracks = scored[:track_count]

    # Shuffle léger pour ne pas avoir tous les artistes groupés
    random.shuffle(final_tracks)

    return {
        "tracks": final_tracks,
        "track_count": len(final_tracks),
        "interpretation": interpretation,
        "search_stats": {
            "total_candidates": len(all_tracks),
            "genres_used": effective_genres,
            "mood_keywords_used": mood_keywords,
            "artists_hinted": artist_hints,
            "energy": energy,
        },
    }
