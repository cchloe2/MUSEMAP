import secrets
import hashlib
import base64
import httpx
from fastapi import APIRouter, HTTPException, Cookie
from fastapi.responses import RedirectResponse, JSONResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

_pkce_store: dict = {}


def _generate_pkce_pair() -> tuple[str, str]:
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@router.get("/login")
def login():
    """Redirige l'utilisateur vers la page de connexion Spotify."""
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
        "show_dialog": "true"
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"https://accounts.spotify.com/authorize?{query}")


@router.get("/callback")
async def callback(code: str, state: str):
    """
    Échange le code Spotify contre un access_token.
    Stocke le token dans un cookie httponly sécurisé.
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
    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token", "")

    # ── Réponse avec cookies httponly (non lisibles par le JS du navigateur) ──
    response = JSONResponse(content={
        "message": "Connexion réussie ✅",
        "expires_in": tokens["expires_in"],
        "scope": tokens.get("scope"),
        # On expose le token ICI uniquement pour les tests /docs
        # En prod : supprimer cette ligne
        "access_token": access_token,
    })

    response.set_cookie(
        key="spotify_access_token",
        value=access_token,
        httponly=True,       # Inaccessible au JavaScript → protège contre XSS
        secure=False,        # Passer à True en prod (HTTPS)
        samesite="lax",      # Protège contre CSRF
        max_age=3600,        # Expire en même temps que le token Spotify
    )
    response.set_cookie(
        key="spotify_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,        # True en prod
        samesite="lax",
        max_age=60 * 60 * 24 * 30,  # 30 jours
    )
    print(f"\n🚀 SCOPES RÉELLEMENT ACCORDÉS PAR SPOTIFY : {tokens.get('scope')}\n")
    
    return response


@router.post("/refresh")
async def refresh_token(
    spotify_refresh_token: str | None = Cookie(default=None),
):
    """
    Renouvelle l'access_token via le refresh_token stocké en cookie.
    """
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
    response = JSONResponse(content={
        "message": "Token renouvelé ✅",
        "expires_in": tokens["expires_in"],
    })
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
    """Supprime les cookies de session."""
    response = JSONResponse(content={"message": "Déconnexion réussie"})
    response.delete_cookie("spotify_access_token")
    response.delete_cookie("spotify_refresh_token")
    return response
