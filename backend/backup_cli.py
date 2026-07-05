import argparse
import os
import sys

# Ajout du répertoire courant au PYTHONPATH pour les imports d'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import load_dotenv
from app.services.connection_service import ConnectionService
from app.repositories import MongoDBRepository
from app.processor import CSVProcessor
from app.domain import ExportRequest
from app.cloud.factory import get_uploader

def main():
    parser = argparse.ArgumentParser(
        description="MongoDB to CSV Cloud Backup CLI - Exécutez et uploadez des exports MongoDB directement depuis le terminal."
    )
    
    # Paramètres MongoDB
    parser.add_argument("--db", required=True, help="Nom de la base de données MongoDB.")
    parser.add_argument("--collection", required=True, help="Nom de la collection à sauvegarder.")
    parser.add_argument("--uri", help="URI complète de connexion MongoDB (écrase les variables d'environnement).")
    parser.add_argument("--cluster", help="Nom d'hôte du cluster MongoDB Atlas (ex: cluster0.xxxx).")
    parser.add_argument("--username", help="Nom d'utilisateur MongoDB.")
    parser.add_argument("--password", help="Mot de passe MongoDB.")
    
    # Paramètres d'export et cloud
    parser.add_argument(
        "--provider", 
        default="mock", 
        choices=["s3", "dropbox", "gdrive", "mock"], 
        help="Fournisseur Cloud de stockage cible (par défaut: mock, écrit dans mock_uploads/)."
    )
    parser.add_argument(
        "--dest", 
        default="backups/mongodb_export.csv", 
        help="Chemin de destination du fichier sur le Cloud."
    )
    parser.add_argument("--env-file", help="Chemin vers un fichier .env personnalisé à charger.")
    
    args = parser.parse_args()
    
    # 1. Chargement des variables d'environnement
    if args.env_file:
        if os.path.exists(args.env_file):
            print(f"Chargement des variables depuis {args.env_file}...")
            with open(args.env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
        else:
            print(f"[ERREUR] Fichier d'environnement spécifié introuvable : {args.env_file}")
            sys.exit(1)
    else:
        load_dotenv()
        
    # 2. Construction de l'URI MongoDB
    mongo_uri = args.uri or os.environ.get("MONGO_URI")
    try:
        req = ExportRequest(
            uri=mongo_uri,
            cluster=args.cluster,
            username=args.username,
            password=args.password,
            db=args.db,
            collection=args.collection
        )
        resolved_uri = ConnectionService.build_mongo_uri(req)
    except Exception as e:
        print(f"[ERREUR] Paramètres MongoDB invalides : {str(e)}")
        sys.exit(1)
        
    # 3. Extraction des documents
    print(f"Connexion à MongoDB...")
    try:
        docs = MongoDBRepository.fetch_documents(resolved_uri, args.db, args.collection)
    except Exception as e:
        print(f"[ERREUR] Connexion à MongoDB ou récupération des données échouée : {str(e)}")
        sys.exit(1)
        
    if not docs:
        print(f"[AVERTISSEMENT] Aucun document trouvé dans {args.db}.{args.collection}. Sauvegarde annulée.")
        sys.exit(0)
        
    # 4. Conversion CSV
    print(f"Normalisation et conversion de {len(docs)} documents en CSV...")
    try:
        df = CSVProcessor.clean_data(docs)
        csv_bytes = CSVProcessor.generate_csv_bytes(df)
    except Exception as e:
        print(f"[ERREUR] Échec de la transformation des données : {str(e)}")
        sys.exit(1)
        
    # 5. Configuration et Factory Cloud
    provider = args.provider.lower()
    config = {}
    
    if provider == "s3":
        config = {
            "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY"),
            "region_name": os.environ.get("AWS_DEFAULT_REGION", "eu-west-3"),
            "bucket_name": os.environ.get("AWS_S3_BUCKET")
        }
    elif provider == "dropbox":
        config = {
            "access_token": os.environ.get("DROPBOX_ACCESS_TOKEN")
        }
    elif provider == "gdrive":
        config = {
            "credentials_file": os.environ.get("GDRIVE_CREDENTIALS_FILE", "credentials.json"),
            "folder_id": os.environ.get("GDRIVE_FOLDER_ID")
        }
        
    print(f"Téléversement du CSV vers '{provider}' (Destination: '{args.dest}')...")
    try:
        uploader = get_uploader(provider, config)
        success = uploader.upload_file(csv_bytes, args.dest)
        if success:
            print(f"[SUCCÈS] Sauvegarde exportée et téléversée avec succès sur {provider} !")
        else:
            print(f"[ERREUR] Échec du téléversement Cloud.")
            sys.exit(1)
    except Exception as e:
        print(f"[ERREUR] Une erreur est survenue lors de l'upload : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
