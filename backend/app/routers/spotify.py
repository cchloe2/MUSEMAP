import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.auth_utils import get_token
from app.services.spotify_client import spotify   # ← instance SpotifyProvider

router = APIRouter(prefix="/spotify", tags=["spotify"])


@router.get("/me")
async def get_current_user(token: str = Depends(get_token)):
    """Profil de l'utilisateur connecté."""
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    u = r.json()
    return {
        "id":           u["id"],
        "display_name": u.get("display_name"),
        "email":        u.get("email"),
        "country":      u.get("country"),
        "product":      u.get("product"),
    }


@router.get("/playlists")
async def get_playlists(
    token: str = Depends(get_token),
    limit: int = Query(default=20, le=50),
):
    """Playlists de l'utilisateur — via SpotifyProvider."""
    try:
        # ✅ spotify.get_user_playlists() — méthode de l'instance, pas du module
        return await spotify.get_user_playlists(token, limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.get("/playlists/{playlist_id}/tracks")
async def get_playlist_tracks(
    playlist_id: str,
    token: str = Depends(get_token),
):
    """Tracks d'une playlist."""
    try:
        return await spotify.get_playlist_tracks(token, playlist_id)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.get("/search")
async def search_tracks(
    genre: str  = Query(..., description="ex: jazz, rock"),
    mood:  str  = Query(default=""),
    limit: int  = Query(default=20, le=50),
    token: str  = Depends(get_token),
):
    """Recherche par genre + mood."""
    try:
        return await spotify.search_tracks_by_genre(token, genre, mood_keywords=mood, limit=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
