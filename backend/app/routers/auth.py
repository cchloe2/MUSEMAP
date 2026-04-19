import secrets
import hashlib
import base64
import httpx
from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

_pkce_store: dict = {}

FRONTEND_URL = "http://localhost:5173"


def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@router.get("/login")
def login():
    code_verifier, code_challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)
    _pkce_store[state] = code_verifier

    params = {
        "response_type": "code",
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "scope": settings.SPOTIFY_SCOPES,
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": code_challenge,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"https://accounts.spotify.com/authorize?{query}")


@router.get("/callback")
async def callback(code: str, state: str):
    """
    Échange le code contre un token.
    Stocke le token en cookie httponly.
    Redirige vers le front React avec le token en paramètre URL
    (pour que sessionStorage puisse le récupérer côté React).
    """
    code_verifier = _pkce_store.pop(state, None)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="State invalide ou expiré")

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
                "client_id": settings.SPOTIFY_CLIENT_ID,
                "code_verifier": code_verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    tokens = r.json()
    access_token  = tokens["access_token"]
    refresh_token = tokens.get("refresh_token", "")

    # ── Redirige vers le front en passant le token dans l'URL ──
    # Le composant Callback.jsx le récupère et le met en sessionStorage
    redirect_url = f"{FRONTEND_URL}/callback?access_token={access_token}"
    response = RedirectResponse(url=redirect_url)

    # Cookie httponly en parallèle (pour les requêtes navigateur directes)
    response.set_cookie(
        key="spotify_access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600,
    )
    response.set_cookie(
        key="spotify_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    return response


@router.post("/refresh")
async def refresh_token(
    spotify_refresh_token: str | None = Cookie(default=None),
):
    if not spotify_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token absent")

    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": spotify_refresh_token,
                "client_id": settings.SPOTIFY_CLIENT_ID,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    tokens = r.json()
    response = JSONResponse(content={"message": "Token renouvelé ✅"})
    response.set_cookie(
        key="spotify_access_token",
        value=tokens["access_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=3600,
    )
    return response


@router.get("/logout")
def logout():
    response = JSONResponse(content={"message": "Déconnexion réussie"})
    response.delete_cookie("spotify_access_token")
    response.delete_cookie("spotify_refresh_token")
    return response
