from fastapi import Cookie, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

# ── Active le bouton "Authorize 🔒" dans /docs ──
bearer_scheme = HTTPBearer(auto_error=False)


async def get_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    spotify_access_token: Optional[str] = Cookie(default=None),
) -> str:
    """
    Résout le token dans cet ordre de priorité :
    1. Header Authorization: Bearer <token>  → utilisé depuis /docs
    2. Cookie httponly spotify_access_token  → utilisé depuis le navigateur

    Lève une 401 claire si aucun token n'est trouvé.
    """
    # Priorité 1 : header Bearer (pratique pour /docs et les tests API)
    if credentials and credentials.credentials:
        return credentials.credentials

    # Priorité 2 : cookie httponly (flux navigateur normal)
    if spotify_access_token:
        return spotify_access_token

    raise HTTPException(
        status_code=401,
        detail="Token manquant. Connecte-toi via /auth/login ou utilise le bouton Authorize dans /docs.",
    )
