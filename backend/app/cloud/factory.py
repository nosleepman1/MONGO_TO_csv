import os
from app.cloud.base import CloudUploader
from app.cloud.s3 import S3Uploader
from app.cloud.dropbox import DropboxUploader
from app.cloud.gdrive import GoogleDriveUploader

class MockUploader(CloudUploader):
    """
    Simulateur de téléversement (Mock) écrivant localement le fichier.
    Très utile pour le développement, le débogage et les tests CI/CD.
    """
    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        # Nettoyage du chemin de destination pour éviter de sortir du répertoire de travail
        safe_path = os.path.basename(destination_path)
        os.makedirs("mock_uploads", exist_ok=True)
        target = os.path.join("mock_uploads", safe_path)
        with open(target, "wb") as f:
            f.write(file_content)
        return True

def get_uploader(provider: str, config: dict = None) -> CloudUploader:
    """
    Factory instanciant l'uploader correspondant au fournisseur spécifié.
    
    :param provider: Le nom du fournisseur ('s3', 'dropbox', 'gdrive', 'mock').
    :param config: Dictionnaire contenant les configurations d'accès requises.
    """
    config = config or {}
    prov = provider.lower().strip()

    if prov == "s3":
        return S3Uploader(
            aws_access_key_id=config.get("aws_access_key_id"),
            aws_secret_access_key=config.get("aws_secret_access_key"),
            region_name=config.get("region_name"),
            bucket_name=config.get("bucket_name")
        )
    elif prov == "dropbox":
        return DropboxUploader(
            access_token=config.get("access_token")
        )
    elif prov in ("gdrive", "google", "google_drive"):
        return GoogleDriveUploader(
            credentials_file=config.get("credentials_file"),
            folder_id=config.get("folder_id")
        )
    elif prov == "mock":
        return MockUploader()
    else:
        raise ValueError(
            f"Fournisseur cloud '{provider}' non reconnu. "
            "Les options valides sont: s3, dropbox, gdrive, mock."
        )
