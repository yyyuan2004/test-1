"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    settings = get_settings()

    # Ensure data directories exist
    settings.faiss_index_dir.mkdir(parents=True, exist_ok=True)
    settings.personas_dir.mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir, "models").mkdir(parents=True, exist_ok=True)

    # Initialize singleton services
    from backend.dependencies import startup, shutdown

    await startup()
    yield
    await shutdown()


def create_app() -> FastAPI:
    app = FastAPI(title="PersonaMirror", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- API routers ---
    from backend.routers import chat, ingest, models, persona, web_learn

    app.include_router(chat.router, prefix="/api")
    app.include_router(ingest.router, prefix="/api")
    app.include_router(persona.router, prefix="/api")
    app.include_router(models.router, prefix="/api")
    app.include_router(web_learn.router, prefix="/api")

    # --- Static frontend ---
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    return app
