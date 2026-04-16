import secrets
import hashlib
import base64
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

# ─── Stockage temporaire du code_verifier (en prod : utiliser Redis/DB) ───
_pkce_store: dict = {}

def _generate_pkce_pair() -> tuple[str, str]:
    """Génère un code_verifier et son code_challenge (PKCE S256)."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return code_verifier, code_challenge


@router.get("/login")
def login():
    """
    Étape 1 : Génère l'URL d'autorisation Spotify et redirige l'utilisateur.
    """
    code_verifier, code_challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    # On stocke le verifier associé au state pour l'étape 3
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
    spotify_auth_url = f"https://accounts.spotify.com/authorize?{query}"

    return RedirectResponse(spotify_auth_url)


@router.get("/callback")
async def callback(code: str, state: str):
    """
    Étape 3 : Spotify renvoie le code ici.
    On l'échange contre un access_token + refresh_token.
    """
    code_verifier = _pkce_store.pop(state, None)
    if not code_verifier:
        raise HTTPException(status_code=400, detail="State invalide ou expiré")

    async with httpx.AsyncClient() as client:
        response = await client.post(
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

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Erreur Spotify : {response.text}"
        )

    tokens = response.json()

    # ─── Pour le MVP : on retourne les tokens directement ───
    # En prod : stocker en DB/session sécurisée, jamais exposer le secret
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens["expires_in"],
        "token_type": tokens["token_type"],
        "scope": tokens.get("scope"),
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """
    Renouvelle l'access_token expiré via le refresh_token.
    À appeler automatiquement quand le token expire (après 3600s).
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.SPOTIFY_CLIENT_ID,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Erreur refresh : {response.text}"
        )

    return response.json()
