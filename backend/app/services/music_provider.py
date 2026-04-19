"""
MusicProvider — Classe de base abstraite pour tous les providers musicaux.

Pattern : Abstract Base Class (ABC)
Ajouter Deezer demain = créer deezer_client.py qui hérite de MusicProvider.
Le reste du code (routers, mood_engine) ne change pas.

Providers prévus :
  - SpotifyProvider  (actif MVP)
  - DeezerProvider   (next)
  - AppleMusicProvider
  - YouTubeMusicProvider
"""

from abc import ABC, abstractmethod
from app.models.schemas import TrackResponse, PlaylistResponse


class MusicProvider(ABC):
    """Interface commune à tous les providers musicaux."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifiant du provider : 'spotify', 'deezer', etc."""
        ...

    # ── Lecture ──────────────────────────────────────────

    @abstractmethod
    async def get_user_playlists(
        self, access_token: str, limit: int = 20
    ) -> list[PlaylistResponse]:
        """Récupère les playlists de l'utilisateur."""
        ...

    @abstractmethod
    async def get_playlist_tracks(
        self, access_token: str, playlist_id: str, limit: int = 50
    ) -> list[TrackResponse]:
        """Récupère les tracks d'une playlist."""
        ...

    @abstractmethod
    async def search_tracks(
        self,
        access_token: str,
        query: str,
        limit: int = 20,
    ) -> list[TrackResponse]:
        """Recherche générique de tracks."""
        ...

    # ── Écriture ─────────────────────────────────────────

    @abstractmethod
    async def create_playlist(
        self,
        access_token: str,
        user_id: str,
        name: str,
        description: str = "",
        public: bool = False,
    ) -> dict:
        """Crée une playlist vide."""
        ...

    @abstractmethod
    async def add_tracks_to_playlist(
        self,
        access_token: str,
        playlist_id: str,
        track_ids: list[str],
    ) -> dict:
        """Ajoute des tracks à une playlist existante."""
        ...

    # ── Utilitaire commun (non-abstrait) ──────────────────

    def format_track_uri(self, track_id: str) -> str:
        """
        Formate un track_id en URI natif du provider.
        Override dans chaque sous-classe si nécessaire.
        """
        return track_id
