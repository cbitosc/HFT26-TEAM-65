"""
FastAPI Server Entry Point
AI-Powered Wildlife Monitoring & Camera-Trap Analytics System
Team 65: The Chosen One | CBIT Hacktoberfest '26
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.backend.config import settings, DATA_DIR, IMAGES_DIR, UPLOADS_DIR
from src.backend.api.routes_detection import router as detection_router
from src.backend.api.routes_analytics import router as analytics_router
from src.backend.api.routes_featherless import router as featherless_router
from src.backend.services.dataset_service import dataset_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure benchmark dataset and sample images exist upon server boot."""
    dataset_service.get_dataset()
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-Powered Wildlife Monitoring & Camera-Trap Analytics System "
        "designed for the Caltech Camera Traps (CCT) dataset benchmark. "
        "Automates animal detection, empty image filtering, species classification "
        "with uncertainty estimation, diel temporal curves, and Featherless AI summaries."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(detection_router)
app.include_router(analytics_router)
app.include_router(featherless_router)

# Mount Static Assets
STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def serve_index():
    """Serves the interactive wildlife analytics dashboard."""
    index_file = STATIC_DIR / "index.html"
    return FileResponse(index_file)

@app.get("/api/health")
async def health_check():
    """System health check and diagnostic status."""
    ds = dataset_service.get_dataset()
    return {
        "status": "online",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "team": settings.team_name,
        "team_id": settings.team_id,
        "workspace_drive": "D:",
        "benchmark_dataset_loaded": ds is not None,
        "total_images_in_benchmark": ds.get("total_images", 243100),
        "dataset_name": "Caltech Camera Traps (CCT-20)",
        "python_version": sys.version
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )
