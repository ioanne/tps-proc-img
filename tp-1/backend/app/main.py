from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  (registers the ORM models in Base.metadata)
from app.config import FRONTEND_DIR, MEDIA_URL, STORAGE_DIR
from app.database import create_tables
from app.errors import register_exception_handlers
from app.routers import images, operations


@asynccontextmanager
async def lifespan(app: FastAPI):
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    create_tables()
    yield


app = FastAPI(
    title="Image Editor — TP 1",
    description="API to upload images and apply edits to them with Pillow / OpenCV.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allows opening the frontend from another origin (e.g. Live Server on :5500).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/api/health", tags=["system"], summary="Server status")
def health():
    return {"status": "ok"}


app.include_router(images.router)
app.include_router(operations.router)

# Image files stored on disk.
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount(MEDIA_URL, StaticFiles(directory=STORAGE_DIR), name="media")

# Frontend (must be mounted last because it captures "/").
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
