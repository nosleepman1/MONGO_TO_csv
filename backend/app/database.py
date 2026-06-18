import urllib.parse
from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from app.models import ExportRequest

def build_mongo_uri(req: ExportRequest) -> str:
    """
    Génère l'URI de connexion MongoDB à partir de la requête.
    Gère l'encodage URL pour l'utilisateur/mot de passe et la correction
    du suffixe d'hôte pour MongoDB Atlas.
    """
    if req.uri:
        return req.uri

    cluster_host = req.cluster
    # Correction du bug Atlas: si l'hôte ne se termine pas par .mongodb.net,
    # et a au plus un point (ex: cluster0 ou cluster0.vvtqpfm), on ajoute .mongodb.net.
    # On évite ainsi de modifier les hôtes complets tiers (ex: mongodb.mondomaine.com).
    if not cluster_host.endswith(".mongodb.net"):
        parts = cluster_host.split('.')
        if len(parts) <= 2:
            cluster_host = f"{cluster_host}.mongodb.net"

    enc_user = urllib.parse.quote_plus(req.username)
    enc_pwd = urllib.parse.quote_plus(req.password)
    return f"mongodb+srv://{enc_user}:{enc_pwd}@{cluster_host}/"


def fetch_mongodb_documents(mongo_uri: str, db_name: str, collection_name: str) -> List[Dict[str, Any]]:
    """
    Se connecte à MongoDB, valide la connexion via ping et récupère tous les documents
    de la collection ciblée. Ferme le client après exécution.
    """
    client = None
    try:
        # serverSelectionTimeoutMS définit le temps maximal d'attente de connexion en millisecondes (5 secondes)
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # Ping la base de données pour vérifier si la connexion est établie et valide
        client.admin.command('ping')
        
        db = client[db_name]
        collection = db[collection_name]
        
        # Récupérer tous les documents
        docs = list(collection.find())
        return docs
        
    except (ConnectionFailure, OperationFailure) as e:
        raise ConnectionError(f"Erreur de connexion MongoDB ou authentification échouée : {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Une erreur est survenue lors de la connexion à MongoDB : {str(e)}")
    finally:
        if client:
            client.close()
