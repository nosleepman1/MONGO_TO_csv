from abc import ABC, abstractmethod

class CloudUploader(ABC):
    """
    Interface abstraite définissant le contrat pour tous les exportateurs Cloud.
    """
    @abstractmethod
    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        """
        Téléverse un fichier sous forme de bytes vers une destination spécifique sur le Cloud.
        
        :param file_content: Le contenu du fichier en octets.
        :param destination_path: Le chemin de destination (nom de clé ou chemin de fichier).
        :return: True si l'upload a réussi, False ou lève une exception sinon.
        """
        pass
