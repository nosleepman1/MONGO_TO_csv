from fastapi import FastAPI
from app.routes import router

# Initialisation de l'application FastAPI
app = FastAPI(
    title="MongoDB to CSV Exporter",
    description="Exportez facilement vos collections MongoDB en fichiers CSV propres.",
    version="1.0.0"
)

# Inclusion des routes
app.include_router(router)
