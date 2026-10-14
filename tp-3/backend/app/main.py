from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import FRONTEND_DIR
from app.errors import register_exception_handlers
from app.routers import avatar, palettes

app = FastAPI(
    title="Retro Avatar — TP 3",
    description="API that turns a photo into a retro pixel-art avatar.",
    version="1.0.0",
)

# Allows opening the frontend from another origin (e.g. Live Server on :5500).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Avatar-Complete"],
)


@app.get("/api/health", tags=["system"], summary="Server status")
def health():
    return {"status": "ok"}


# Domain exceptions (core and API) → {"detail": {"code", "message"}} responses.
register_exception_handlers(app)

app.include_router(palettes.router)
app.include_router(avatar.router)

# Frontend (must be mounted last because it captures "/").
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
