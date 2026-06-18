import os

# Dossier racine du projet backend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Chemin d'accès absolu au fichier index.html de l'interface utilisateur
INDEX_HTML_PATH = os.path.join(BASE_DIR, "index.html")
if not os.path.exists(INDEX_HTML_PATH):
    INDEX_HTML_PATH = os.path.join(os.path.dirname(BASE_DIR), "index.html")

def load_dotenv():
    """
    Chargeur léger de variables d'environnement depuis un fichier .env (sans dépendance tierce).
    Utile pour la portabilité et le fonctionnement sans installation additionnelle.
    """
    # Recherche dans backend/.env, et sinon à la racine du workspace
    dotenv_path = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(dotenv_path):
        dotenv_path = os.path.join(os.path.dirname(BASE_DIR), ".env")

    if os.path.exists(dotenv_path):
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip()
                # Enlever les éventuels guillemets englobants
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                if key:
                    os.environ[key] = val

# Charger le fichier .env au démarrage du module config
load_dotenv()

# MongoDB Configuration par défaut (optionnelle si fournie en paramètre API ou CLI)
MONGO_URI = os.environ.get("MONGO_URI", "")

# Configuration de la Planification Automatique
BACKUP_SCHEDULE_HOUR = int(os.environ.get("BACKUP_SCHEDULE_HOUR", "2"))
BACKUP_SCHEDULE_MINUTE = int(os.environ.get("BACKUP_SCHEDULE_MINUTE", "0"))
BACKUP_DB_NAME = os.environ.get("BACKUP_DB_NAME", "")
BACKUP_COLLECTION_NAME = os.environ.get("BACKUP_COLLECTION_NAME", "")
BACKUP_CLOUD_PROVIDER = os.environ.get("BACKUP_CLOUD_PROVIDER", "s3")
BACKUP_DEST_PATH = os.environ.get("BACKUP_DEST_PATH", "backups/mongodb_export.csv")

# Configuration AWS S3
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-west-3")
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "")

# Configuration Dropbox
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN", "")

# Configuration Google Drive
GDRIVE_CREDENTIALS_FILE = os.environ.get("GDRIVE_CREDENTIALS_FILE", "credentials.json")
GDRIVE_FOLDER_ID = os.environ.get("GDRIVE_FOLDER_ID", "")
