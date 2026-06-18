import logging
from app.database import fetch_mongodb_documents, build_mongo_uri
from app.processor import clean_data, generate_csv_bytes
from app.cloud.factory import get_uploader

logger = logging.getLogger("app.scheduler.tasks")

def run_backup_job(
    db_name: str,
    collection_name: str,
    provider: str,
    dest_path: str,
    mongo_uri: str = None,
    connection_details: dict = None,
    provider_config: dict = None
):
    """
    Tâche planifiée pour exécuter un export et un upload Cloud complet.
    
    :param db_name: Nom de la base de données.
    :param collection_name: Nom de la collection.
    :param provider: Fournisseur Cloud ('s3', 'dropbox', 'gdrive', 'mock').
    :param dest_path: Chemin de destination du fichier exporté.
    :param mongo_uri: URI complète de connexion (alternative aux détails séparés).
    :param connection_details: Dictionnaire avec cluster, username, password.
    :param provider_config: Paramètres du fournisseur Cloud (tokens, buckets...).
    """
    logger.info(f"Début de la tâche de sauvegarde: {db_name}.{collection_name} -> {provider} ({dest_path})")
    
    try:
        # Résolution de l'URI de connexion MongoDB
        uri = mongo_uri
        if not uri and connection_details:
            # Reconstruire les détails avec ExportRequest ou directement la méthode build_mongo_uri
            from app.models import ExportRequest
            req = ExportRequest(
                cluster=connection_details.get("cluster"),
                username=connection_details.get("username"),
                password=connection_details.get("password"),
                db=db_name,
                collection=collection_name
            )
            uri = build_mongo_uri(req)
            
        if not uri:
            raise ValueError("Aucune URI ou détail de connexion MongoDB fourni pour la tâche.")

        # 1. Extraction MongoDB
        docs = fetch_mongodb_documents(uri, db_name, collection_name)
        if not docs:
            logger.warning(f"Aucun document extrait de la collection '{collection_name}'. Tâche annulée.")
            return False

        # 2. Conversion CSV
        df = clean_data(docs)
        csv_bytes = generate_csv_bytes(df)

        # 3. Uploader Cloud
        uploader = get_uploader(provider, provider_config)
        success = uploader.upload_file(csv_bytes, dest_path)
        
        if success:
            logger.info(f"Tâche de sauvegarde réussie: {db_name}.{collection_name} téléversée sur {provider}.")
            return True
        else:
            logger.error(f"Échec de l'upload cloud pour la tâche de sauvegarde de {db_name}.{collection_name}.")
            return False
            
    except Exception as e:
        logger.error(f"Erreur fatale lors de la tâche de sauvegarde de {db_name}.{collection_name}: {str(e)}", exc_info=True)
        raise e
