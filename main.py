import uvicorn
from app.main import app

# Ce fichier sert de point d'entrée pour lancer l'application.
# Il est compatible avec 'uvicorn main:app' et 'python main.py'.

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)