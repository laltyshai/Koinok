"""
main.py
-------
Application entry point.

Responsibilities:
  - Instantiate the FastAPI app
  - Configure CORS (permissive for Flutter local dev — tighten in production)
  - Create all SQLAlchemy tables on startup
  - Mount feature routers
  - Expose GET /health
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth as auth_router, wardrobe

# ---------------------------------------------------------------------------
# Create tables
# ---------------------------------------------------------------------------
# This runs Base.metadata.create_all() at import time so the first request
# never hits a missing-table error.  In production you'd use Alembic instead.
Base.metadata.create_all(bind=engine)

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

# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"], summary="Server health check")
def health():
    """Returns 200 OK when the server is running."""
    return {"status": "ok"}
