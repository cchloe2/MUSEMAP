from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, spotify

app = FastAPI(
    title="MuseMap API",
    description="Genre & mood-based AI playlist generator",
    version="0.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ───
app.include_router(auth.router)
app.include_router(spotify.router)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "project": "MuseMap",
        "phase": 1,
        "step": 2,
        "auth": "OAuth2 PKCE ready"
    }
