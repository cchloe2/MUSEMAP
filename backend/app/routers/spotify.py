import httpx
from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/spotify", tags=["spotify"])


@router.get("/me")
async def get_current_user(authorization: str = Header(...)):
    """
    Récupère le profil de l'utilisateur connecté.
    Header attendu : Authorization: Bearer <access_token>
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": authorization},
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Erreur Spotify : {response.text}"
        )

    user = response.json()

    # On retourne uniquement ce dont on a besoin (Data Analyst mindset)
    return {
        "id": user["id"],
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "country": user.get("country"),
        "product": user.get("product"),  # "premium" ou "free"
        "followers": user.get("followers", {}).get("total"),
    }
