import io
import urllib.parse
from typing import Optional
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, model_validator
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

app = FastAPI(
    title="MongoDB to CSV Exporter",
    description="Exportez facilement vos collections MongoDB en fichiers CSV propres.",
    version="1.0.0"
)

class ExportRequest(BaseModel):
    uri: Optional[str] = None
    cluster: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    db: str
    collection: str

    @model_validator(mode="after")
    def check_credentials(self) -> "ExportRequest":
        if not self.uri:
            if not all([self.cluster, self.username, self.password]):
                raise ValueError(
                    "Vous devez fournir soit une 'URI de connexion', soit le triplet ('Cluster', 'Utilisateur', 'Mot de passe')."
                )
        return self

def clean_data(docs: list) -> pd.DataFrame:
    """
    Normalise les documents MongoDB en DataFrame pandas propre :
    - Exclut la colonne '_id'
    - Aplatit les structures de dictionnaires imbriquées (ex: user.name)
    - Joint les listes/tableaux sous forme de chaînes de caractères séparées par des virgules (ex: tags)
    """
    if not docs:
        return pd.DataFrame()
        
    # Normalise les structures imbriquées (dictionnaires)
    df = pd.json_normalize(docs)
    
    # Exclure le champ _id s'il est présent
    if "_id" in df.columns:
        df = df.drop(columns=["_id"])
        
    # Traiter les listes (ex: tags, arrays) pour les transformer en chaînes propres séparées par des virgules
    for col in df.columns:
        # On vérifie si au moins une ligne de cette colonne contient une liste
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(
                lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
            )
            
    return df

@app.get("/", response_class=HTMLResponse)
def read_root():
    """
    Sert l'interface utilisateur web interactive de l'application.
    """
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du chargement de l'interface utilisateur : {str(e)}"
        )

@app.post("/export-csv")
def export_csv(req: ExportRequest):
    """
    Endpoint POST qui reçoit les identifiants/URI MongoDB,
    se connecte à la collection cible, nettoie les données et renvoie un CSV propre.
    """
    # 1. Déterminer l'URI de connexion
    if req.uri:
        mongo_uri = req.uri
    else:
        # Si le cluster ne contient pas de point ou ne finit pas par mongodb.net, on ajoute .mongodb.net
        cluster_host = req.cluster
        if not cluster_host.endswith(".mongodb.net") and "." not in cluster_host:
            cluster_host = f"{cluster_host}.mongodb.net"
            
        enc_user = urllib.parse.quote_plus(req.username)
        enc_pwd = urllib.parse.quote_plus(req.password)
        mongo_uri = f"mongodb+srv://{enc_user}:{enc_pwd}@{cluster_host}/"

    # 2. Se connecter à MongoDB et récupérer la collection
    client = None
    try:
        # serverSelectionTimeoutMS définit le temps maximal d'attente de connexion en millisecondes (5 secondes)
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        
        # ping la base de données pour vérifier si la connexion est établie et valide
        client.admin.command('ping')
        
        db = client[req.db]
        collection = db[req.collection]
        
        # Récupérer tous les documents
        docs = list(collection.find())
        
    except (ConnectionFailure, OperationFailure) as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur de connexion MongoDB ou authentification échouée : {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Une erreur est survenue lors de la connexion à MongoDB : {str(e)}"
        )
    finally:
        if client:
            client.close()

    # Si aucun document n'est présent dans la collection
    if not docs:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun document trouvé dans la collection '{req.collection}' de la base '{req.db}'."
        )

    # 3. Formater les données en CSV propre
    try:
        df = clean_data(docs)
        
        # Générer le CSV en mémoire (Stream) avec UTF-8 BOM pour Excel
        stream = io.StringIO()
        df.to_csv(stream, index=False, encoding="utf-8-sig")
        csv_content = stream.getvalue()
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du CSV : {str(e)}"
        )

    # Retourner le flux du fichier CSV
    filename = f"{req.collection}_export.csv"
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )