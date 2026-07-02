from contextlib import asynccontextmanager
from fastapi import FastAPI
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

# Include routes
app.include_router(router)
