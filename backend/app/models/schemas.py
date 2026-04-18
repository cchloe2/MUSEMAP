from pydantic import BaseModel
from typing import Optional, List


# ─── Track ───────────────────────────────────────────────
class TrackBase(BaseModel):
    spotify_id: str
    name: str
    artist: str
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    popularity: Optional[int] = None      # 0-100, utile pour filtrer
    preview_url: Optional[str] = None
    genres: Optional[List[str]] = []      # genres associés à l'artiste


class TrackResponse(TrackBase):
    """Ce qu'on retourne à l'API"""
    spotify_url: Optional[str] = None
    image_url: Optional[str] = None       # cover de l'album


# ─── Playlist ────────────────────────────────────────────
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


# ─── Requête de génération (cœur du produit) ─────────────
class GeneratePlaylistRequest(BaseModel):
    prompt: str                           # ex: "Soirée jazz cosy à Paris"
    genres: Optional[List[str]] = []      # ex: ["jazz", "soul"]
    mood: Optional[str] = None            # ex: "relax"
    track_count: int = 20                 # nombre de titres souhaité


# ─── Données analytiques (notre dataset maison) ──────────
class TrackAnalytics(BaseModel):
    """
    Structure pour notre future base analytique.
    Remplace les Audio Features Spotify qu'on ne peut plus utiliser.
    On enrichit progressivement via les inputs utilisateurs.
    """
    spotify_id: str
    user_prompt: Optional[str] = None     # le prompt qui a généré ce track
    user_mood: Optional[str] = None       # mood assigné par l'utilisateur
    user_genres: Optional[List[str]] = [] # genres choisis
    popularity: Optional[int] = None
    added_to_playlist_count: int = 0      # combien de fois ce track a été choisi
