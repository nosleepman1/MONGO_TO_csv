from app.cloud.base import CloudUploader

class DropboxUploader(CloudUploader):
    """
    Gestionnaire d'upload pour Dropbox. Importe dropbox de manière dynamique.
    """
    def __init__(self, access_token: str = None):
        self.access_token = access_token

    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        """
        Téléverse le contenu du fichier (bytes) vers l'espace Dropbox spécifié.
        """
        try:
            import dropbox
        except ImportError:
            raise ImportError(
                "Le package 'dropbox' est requis pour utiliser Dropbox. "
                "Veuillez l'installer en exécutant 'pip install dropbox'."
            )

        if not self.access_token:
            raise ValueError("Le jeton d'accès Dropbox (DROPBOX_ACCESS_TOKEN) n'est pas configuré.")

        # Dropbox requiert que le chemin commence par un slash
        path = destination_path if destination_path.startswith("/") else f"/{destination_path}"

        try:
            dbx = dropbox.Dropbox(self.access_token)
            dbx.files_upload(
                file_content,
                path,
                mode=dropbox.files.WriteMode.overwrite
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'upload vers Dropbox: {str(e)}")
