import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routes.api import router
from app.scheduler.manager import scheduler_manager
from app.core.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown event handler"""
    logger.info("Application starting...")
    scheduler_manager.start()
    yield
    logger.info("Application shutting down...")
    scheduler_manager.shutdown()

# Initialization
app = FastAPI(
    title="MongoDB to CSV Exporter",
    description="Export MongoDB collections to clean CSV files and schedule cloud backups.",
    version="1.1.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files if frontend build exists
frontend_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    assets_dir = os.path.join(frontend_dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# Include routes
app.include_router(router)
