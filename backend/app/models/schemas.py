from pydantic import BaseModel
from typing import Optional, List


class TrackBase(BaseModel):
    spotify_id: str
    name: str
    artist: str
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None
    preview_url: Optional[str] = None
    genres: Optional[List[str]] = []


class TrackResponse(TrackBase):
    spotify_url: Optional[str] = None
    image_url: Optional[str] = None
    release_year: Optional[int] = None     # ← nouveau : pour filtre année
    isrc: Optional[str] = None             # ← nouveau : export CSV universel
    bpm: Optional[float] = None            # ← réservé (source externe future)
    energy: Optional[float] = None         # ← réservé (source externe future)
    valence: Optional[float] = None        # ← réservé (source externe future)


class PlaylistBase(BaseModel):
    spotify_id: str
    name: str
    description: Optional[str] = None
    track_count: Optional[int] = None
    owner_id: Optional[str] = None


class PlaylistResponse(PlaylistBase):
    image_url: Optional[str] = None
    spotify_url: Optional[str] = None
    tracks: Optional[List[TrackResponse]] = []


class GeneratePlaylistRequest(BaseModel):
    prompt: str
    genres: Optional[List[str]] = []
    mood: Optional[str] = None
    track_count: int = 20


# ── Studio : requête de filtrage ─────────────────────────
class StudioFilterRequest(BaseModel):
    """
    Filtres appliqués sur une sélection de playlists existantes.
    Tous les champs sont optionnels — on filtre uniquement ce qui est fourni.
    """
    playlist_ids: List[str]                   # IDs Spotify des playlists sources
    genres: Optional[List[str]] = []          # ex: ["jazz", "soul"]
    year_min: Optional[int] = None            # ex: 2010
    year_max: Optional[int] = None            # ex: 2024
    popularity_min: Optional[int] = None      # 0-100
    popularity_max: Optional[int] = None      # 0-100
    bpm_min: Optional[float] = None           # réservé
    bpm_max: Optional[float] = None           # réservé


# ── Studio : payload d'export Spotify ────────────────────
class ExportToSpotifyRequest(BaseModel):
    track_ids: List[str]                      # IDs bruts Spotify
    playlist_name: str = "MuseMap Export"
    public: bool = False                      # privé par défaut


# ── Analytics (dataset maison) ───────────────────────────
class TrackAnalytics(BaseModel):
    spotify_id: str
    user_prompt: Optional[str] = None
    user_mood: Optional[str] = None
    user_genres: Optional[List[str]] = []
    popularity: Optional[int] = None
    added_to_playlist_count: int = 0
