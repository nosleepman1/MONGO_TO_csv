import os

# Dossier racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chemin d'accès absolu au fichier index.html de l'interface utilisateur
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
