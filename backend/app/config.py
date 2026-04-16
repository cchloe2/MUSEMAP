from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    SPOTIFY_REDIRECT_URI: str = os.getenv(
        "SPOTIFY_REDIRECT_URI",
        "http://127.0.0.1:8000/auth/callback"
    )
    SPOTIFY_SCOPES: str = " ".join([
        "playlist-modify-public",
        "playlist-modify-private",
        "playlist-read-private",
        "user-read-private",
        "user-read-email",
    ])

settings = Settings()
