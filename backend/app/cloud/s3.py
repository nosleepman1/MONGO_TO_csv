import io
from app.cloud.base import CloudUploader

class S3Uploader(CloudUploader):
    """
    Gestionnaire d'upload pour Amazon S3. Importe boto3 de manière dynamique.
    """
    def __init__(self, aws_access_key_id: str = None, aws_secret_access_key: str = None, region_name: str = None, bucket_name: str = None):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.bucket_name = bucket_name

    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        """
        Téléverse le contenu du fichier (bytes) vers le bucket AWS S3 spécifié.
        """
        try:
            import boto3
        except ImportError:
            raise ImportError(
                "Le package 'boto3' est requis pour utiliser AWS S3. "
                "Veuillez l'installer en exécutant 'pip install boto3'."
            )

        if not self.bucket_name:
            raise ValueError("Le nom du bucket AWS S3 (AWS_S3_BUCKET) n'est pas configuré.")

        # Configuration des identifiants
        client_kwargs = {}
        if self.aws_access_key_id and self.aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = self.aws_access_key_id
            client_kwargs["aws_secret_access_key"] = self.aws_secret_access_key
        if self.region_name:
            client_kwargs["region_name"] = self.region_name

        try:
            s3_client = boto3.client('s3', **client_kwargs)
            s3_client.upload_fileobj(
                io.BytesIO(file_content),
                self.bucket_name,
                destination_path
            )
            return True
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'upload vers S3: {str(e)}")
