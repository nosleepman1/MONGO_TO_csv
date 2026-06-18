from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routes import router
from app.scheduler.manager import scheduler_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage automatique d'APScheduler au lancement du serveur
    scheduler_manager.start()
    yield
    # Arrêt propre d'APScheduler à l'arrêt du serveur
    scheduler_manager.shutdown()

# Initialisation de l'application FastAPI
app = FastAPI(
    title="MongoDB to CSV Exporter",
    description="Exportez facilement vos collections MongoDB en fichiers CSV propres et planifiez des sauvegardes cloud.",
    version="1.1.0",
    lifespan=lifespan
)

# Inclusion des routes
app.include_router(router)
