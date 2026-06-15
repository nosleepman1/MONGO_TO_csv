from abc import ABC, abstractmethod

class CloudUploader(ABC):
    @abstractmethod
    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        """
        Méthode abstraite d'upload de données binaires vers un stockage Cloud.
        
        :param file_content: Les octets (bytes) du fichier à uploader.
        :param destination_path: Le chemin ou nom de clé de destination dans le cloud.
        :return: True si l'upload a réussi, lève une exception en cas d'erreur.
        """
        pass
