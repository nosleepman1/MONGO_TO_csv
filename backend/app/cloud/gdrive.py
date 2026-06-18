import io
import os
from app.cloud.base import CloudUploader

class GoogleDriveUploader(CloudUploader):
    """
    Gestionnaire d'upload pour Google Drive. Importe googleapiclient de manière dynamique.
    """
    def __init__(self, credentials_file: str = "credentials.json", folder_id: str = None):
        self.credentials_file = credentials_file
        self.folder_id = folder_id

    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        """
        Téléverse le contenu du fichier (bytes) vers Google Drive.
        """
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseUpload
        except ImportError:
            raise ImportError(
                "Les bibliothèques Google APIs sont requises pour utiliser Google Drive. "
                "Veuillez les installer en exécutant: "
                "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )

        if not self.credentials_file:
            raise ValueError("Le chemin du fichier de credentials Google Drive (GDRIVE_CREDENTIALS_FILE) n'est pas configuré.")

        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Le fichier de clés Google Drive est introuvable à l'adresse: '{self.credentials_file}'. "
                "Veuillez vérifier son emplacement."
            )

        try:
            # Authentification par compte de service
            scopes = ['https://www.googleapis.com/auth/drive']
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )

            service = build('drive', 'v3', credentials=credentials)

            # Extraction du nom du fichier
            filename = os.path.basename(destination_path)

            file_metadata = {
                'name': filename
            }

            # Si un dossier cible est spécifié, on ajoute le parent
            if self.folder_id:
                file_metadata['parents'] = [self.folder_id]

            media = MediaIoBaseUpload(
                io.BytesIO(file_content),
                mimetype='text/csv',
                resumable=True
            )

            service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()

            return True
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'upload vers Google Drive: {str(e)}")
