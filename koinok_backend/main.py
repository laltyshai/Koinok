"""
main.py
-------
Application entry point.

Responsibilities:
  - Instantiate the FastAPI app
  - Configure CORS (permissive for Flutter local dev — tighten in production)
  - Apply pending Alembic migrations on startup
  - Mount feature routers
  - Expose GET /health
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from routers import auth as auth_router, wardrobe
from routers import calendar as calendar_router
from routers import looks as looks_router


# ---------------------------------------------------------------------------
# Apply migrations
# ---------------------------------------------------------------------------
# Runs at import time so the schema is always up to date before the first
# request, same zero-step behaviour as before, but now backed by real
# Alembic revisions instead of ad-hoc create_all()/ALTER TABLE.
_alembic_cfg = Config(str(Path(__file__).parent / "alembic.ini"))
command.upgrade(_alembic_cfg, "head")

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Koinok — E-Wardrobe API",
    description=(
        "Backend for the E-Wardrobe mobile application. "
        "Manage your closet, track daily outfits, and discover forgotten favourites."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow Flutter app to connect from any local IP during development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Restrict to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router.router)
app.include_router(wardrobe.router)
app.include_router(calendar_router.router)
app.include_router(looks_router.router)

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"], summary="Server health check")
def health():
    """Returns 200 OK when the server is running."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------
@app.get("/", response_class=PlainTextResponse, tags=["System"], summary="Root endpoint")
def index():
    """Returns a simple text indicating the service is running."""
    return "Koinok is alive"

