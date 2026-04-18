import httpx
from typing import Optional
from app.models.schemas import TrackResponse, PlaylistResponse

SPOTIFY_BASE = "https://api.spotify.com/v1"


def _headers(access_token: str) -> dict:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


# ════════════════════════════════════════════
#  PLAYLISTS
# ════════════════════════════════════════════

async def get_user_playlists(
    access_token: str,
    limit: int = 20
) -> list[PlaylistResponse]:
    """Récupère les playlists de l'utilisateur connecté."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_BASE}/me/playlists",
            headers=_headers(access_token),
            params={"limit": limit},
        )
        r.raise_for_status()

    playlists = []
    for item in r.json().get("items", []):
        if not item:
            continue
        images = item.get("images", [])
        playlists.append(PlaylistResponse(
            spotify_id=item["id"],
            name=item["name"],
            description=item.get("description"),
            track_count=item.get("tracks", {}).get("total"),
            owner_id=item.get("owner", {}).get("id"),
            image_url=images[0]["url"] if images else None,
            spotify_url=item.get("external_urls", {}).get("spotify"),
        ))
    return playlists


async def get_playlist_tracks(
    access_token: str,
    playlist_id: str,
    limit: int = 50
) -> list[TrackResponse]:
    """Récupère les tracks d'une playlist spécifique."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_BASE}/playlists/{playlist_id}/tracks",
            headers=_headers(access_token),
            params={"limit": limit, "fields": "items(track(id,name,artists,album,duration_ms,popularity,preview_url,external_urls))"},
        )
        r.raise_for_status()

    tracks = []
    for item in r.json().get("items", []):
        track = item.get("track")
        if not track or not track.get("id"):
            continue
        tracks.append(_normalize_track(track))
    return tracks


# ════════════════════════════════════════════
#  SEARCH — cœur du moteur de recommandation
# ════════════════════════════════════════════

async def search_tracks_by_genre(
    access_token: str,
    genre: str,
    mood_keywords: Optional[str] = None,
    limit: int = 20,
) -> list[TrackResponse]:
    """
    Recherche des tracks par genre + mots-clés de mood.
    Ex: genre="jazz", mood_keywords="calm night cosy"
    → query Spotify: "genre:jazz calm night cosy"
    """
    query = f"genre:{genre}"
    if mood_keywords:
        query += f" {mood_keywords}"

    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_BASE}/search",
            headers=_headers(access_token),
            params={
                "q": query,
                "type": "track",
                "limit": limit,
                "market": "FR",
            },
        )
        r.raise_for_status()

    tracks = []
    for item in r.json().get("tracks", {}).get("items", []):
        if item:
            tracks.append(_normalize_track(item))
    return tracks


async def search_tracks_by_artist(
    access_token: str,
    artist: str,
    limit: int = 10,
) -> list[TrackResponse]:
    """Recherche des tracks d'un artiste spécifique."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"{SPOTIFY_BASE}/search",
            headers=_headers(access_token),
            params={
                "q": f"artist:{artist}",
                "type": "track",
                "limit": limit,
                "market": "FR",
            },
        )
        r.raise_for_status()

    return [_normalize_track(t) for t in r.json().get("tracks", {}).get("items", []) if t]


# ════════════════════════════════════════════
#  CRÉATION DE PLAYLIST
# ════════════════════════════════════════════

async def create_playlist(
    access_token: str,
    user_id: str,
    name: str,
    description: str = "",
    public: bool = True,
) -> dict:
    """Crée une nouvelle playlist vide sur le compte utilisateur."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SPOTIFY_BASE}/users/{user_id}/playlists",
            headers={**_headers(access_token), "Content-Type": "application/json"},
            json={"name": name, "description": description, "public": False},
        )
        r.raise_for_status()
    return r.json()


async def add_tracks_to_playlist(
    access_token: str,
    playlist_id: str,
    track_uris: list[str],
) -> dict:
    """Ajoute une liste de tracks (URIs Spotify) à une playlist."""
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{SPOTIFY_BASE}/playlists/{playlist_id}/tracks",
            headers={**_headers(access_token), "Content-Type": "application/json"},
            json={"uris": track_uris},
        )
        r.raise_for_status()
    return r.json()


# ════════════════════════════════════════════
#  UTILITAIRE — Normalisation
# ════════════════════════════════════════════

def _normalize_track(raw: dict) -> TrackResponse:
    """
    Transforme la réponse brute Spotify en TrackResponse normalisé.
    Centraliser ici = un seul endroit à modifier si l'API change.
    """
    artists = raw.get("artists", [])
    artist_name = ", ".join(a["name"] for a in artists) if artists else "Inconnu"

    album = raw.get("album", {})
    images = album.get("images", [])

    return TrackResponse(
        spotify_id=raw["id"],
        name=raw.get("name", ""),
        artist=artist_name,
        album=album.get("name"),
        duration_ms=raw.get("duration_ms"),
        popularity=raw.get("popularity"),
        preview_url=raw.get("preview_url"),
        spotify_url=raw.get("external_urls", {}).get("spotify"),
        image_url=images[0]["url"] if images else None,
    )
