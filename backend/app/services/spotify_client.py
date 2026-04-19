"""
SpotifyProvider — Implémentation Spotify de MusicProvider.
Toute la logique Spotify est ici, isolée du reste.
"""

import httpx
from app.services.music_provider import MusicProvider
from app.models.schemas import TrackResponse, PlaylistResponse

SPOTIFY_BASE = "https://api.spotify.com/v1"


def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


class SpotifyProvider(MusicProvider):

    @property
    def provider_name(self) -> str:
        return "spotify"

    def format_track_uri(self, track_id: str) -> str:
        raw = track_id.strip()
        if raw.startswith("spotify:track:"):
            return raw
        return f"spotify:track:{raw}"

    async def get_user_playlists(
        self, access_token: str, limit: int = 20
    ) -> list[PlaylistResponse]:
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
        self, access_token: str, playlist_id: str, limit: int = 50
    ) -> list[TrackResponse]:
        tracks = []
        url = f"{SPOTIFY_BASE}/playlists/{playlist_id}/tracks"
        params = {
            "limit": limit,
            "fields": "items(track(id,name,artists,album,duration_ms,popularity,preview_url,external_urls,external_ids)),next",
        }
        async with httpx.AsyncClient() as client:
            while url:
                r = await client.get(url, headers=_headers(access_token), params=params)
                r.raise_for_status()
                data = r.json()
                for item in data.get("items", []):
                    track = item.get("track")
                    if track and track.get("id"):
                        tracks.append(_normalize_track(track))
                url = data.get("next")
                params = {}   # next url contient déjà les params
        return tracks

    async def search_tracks(
        self,
        access_token: str,
        query: str,
        limit: int = 20,
    ) -> list[TrackResponse]:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f"{SPOTIFY_BASE}/search",
                headers=_headers(access_token),
                params={"q": query, "type": "track", "limit": limit, "market": "FR"},
            )
            r.raise_for_status()
        return [
            _normalize_track(t)
            for t in r.json().get("tracks", {}).get("items", [])
            if t
        ]

    async def search_tracks_by_genre(
        self,
        access_token: str,
        genre: str,
        mood_keywords: str | None = None,
        limit: int = 20,
    ) -> list[TrackResponse]:
        query = f"genre:{genre}"
        if mood_keywords:
            query += f" {mood_keywords}"
        return await self.search_tracks(access_token, query, limit)

    async def search_tracks_by_artist(
        self,
        access_token: str,
        artist: str,
        limit: int = 10,
    ) -> list[TrackResponse]:
        return await self.search_tracks(access_token, f"artist:{artist}", limit)

    async def create_playlist(
        self,
        access_token: str,
        user_id: str,
        name: str,
        description: str = "",
        public: bool = False,
    ) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{SPOTIFY_BASE}/users/{user_id}/playlists",
                headers={**_headers(access_token), "Content-Type": "application/json"},
                json={"name": name, "description": description, "public": public},
            )
            r.raise_for_status()
        return r.json()

    async def add_tracks_to_playlist(
        self,
        access_token: str,
        playlist_id: str,
        track_ids: list[str],
    ) -> dict:
        """Accepte des IDs bruts — formate en URIs automatiquement."""
        uris = [self.format_track_uri(tid) for tid in track_ids]
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{SPOTIFY_BASE}/playlists/{playlist_id}/tracks",
                headers={**_headers(access_token), "Content-Type": "application/json"},
                json={"uris": uris},
            )
            r.raise_for_status()
        return r.json()


# ── Singleton — importé partout dans le projet ──
spotify = SpotifyProvider()


# ── Normalisation interne ─────────────────────────────────
def _normalize_track(raw: dict) -> TrackResponse:
    artists = raw.get("artists", [])
    artist_name = ", ".join(a["name"] for a in artists) if artists else "Inconnu"
    album = raw.get("album", {})
    images = album.get("images", [])
    release = album.get("release_date", "")
    year = int(release[:4]) if release and len(release) >= 4 else None
    isrc = raw.get("external_ids", {}).get("isrc")

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
        release_year=year,
        isrc=isrc,
    )
