"""FastAPI application entry point for Rezno AI research intelligence engine."""

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from backend.api.routes.citations import router as citations_router
from backend.api.routes.search import router as search_router

logger = logging.getLogger("rezno.api")

# Initialize FastAPI application
app = FastAPI(
    title="Rezno AI API",
    version="0.2.0",
    description="Academic literature intelligence engine with grounded claim verification.",
)

# Enable CORS for unrestricted local and web client access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(search_router)
app.include_router(citations_router)


@app.get("/api/health", tags=["system"])
async def health_check():
    """Health check endpoint for container probes and UI resilience checks."""
    return {
        "status": "healthy",
        "service": "rezno-ai",
        "version": "0.2.0",
    }


# Mount static frontend directory safely if present
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"

if FRONTEND_DIR.is_dir():
    logger.info(f"Mounting static frontend assets from {FRONTEND_DIR}")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
elif os.path.isdir("frontend"):
    logger.info("Mounting static frontend assets from ./frontend")
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
else:
    logger.warning("Frontend directory not detected; root static mounting skipped.")

    @app.get("/", tags=["system"])
    async def index_fallback():
        return {
            "status": "healthy",
            "service": "rezno-ai",
            "version": "0.2.0",
            "message": "Frontend static files pending. API is active.",
        }
