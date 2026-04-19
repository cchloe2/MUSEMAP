from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from app.routers import auth, spotify, playlist, studio

bearer_scheme = HTTPBearer(auto_error=False)

app = FastAPI(
    title="MuseMap API",
    description="Cross-platform music management hub",
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(spotify.router)
app.include_router(playlist.router)
app.include_router(studio.router)

@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "ok",
        "project": "MuseMap",
        "version": "0.5.0",
        "phase": "3 - Studio",
    }
