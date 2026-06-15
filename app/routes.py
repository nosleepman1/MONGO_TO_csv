import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import INDEX_HTML_PATH
from app.models import ExportRequest
from app.database import build_mongo_uri, fetch_mongodb_documents
from app.processor import clean_data, generate_csv_bytes, sanitize_filename

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def read_root():
    """
    Sert l'interface utilisateur web interactive de l'application.
    Utilise le chemin d'accès absolu résolu pour éviter les erreurs de répertoire de travail.
    """
    try:
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du chargement de l'interface utilisateur : {str(e)}"
        )


@router.post("/export-csv")
def export_csv(req: ExportRequest):
    """
    Endpoint POST qui reçoit les identifiants/URI MongoDB,
    se connecte à la collection cible, nettoie les données et renvoie un CSV propre.
    """
    # 1. Déterminer l'URI de connexion
    try:
        mongo_uri = build_mongo_uri(req)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de la construction de l'URI de connexion : {str(e)}"
        )

    # 2. Se connecter et récupérer les documents de la collection
    try:
        docs = fetch_mongodb_documents(mongo_uri, req.db, req.collection)
    except ConnectionError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    # 3. Vérifier s'il y a des documents dans la collection
    if not docs:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun document trouvé dans la collection '{req.collection}' de la base '{req.db}'."
        )

    # 4. Formater les données en CSV propre
    try:
        df = clean_data(docs)
        csv_bytes = generate_csv_bytes(df)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération du CSV : {str(e)}"
        )

    # 5. Assainir le nom de fichier et retourner le flux
    raw_filename = f"{req.collection}_export.csv"
    filename = sanitize_filename(raw_filename)
    
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )
