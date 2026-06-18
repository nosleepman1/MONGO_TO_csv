import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import INDEX_HTML_PATH
from app.models import ExportRequest, BackupRequest, ScheduleRequest
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
@router.post("/api/export-csv")
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


@router.post("/api/backup")
def run_backup(req: BackupRequest):
    """
    Déclenche immédiatement une sauvegarde MongoDB et la téléverse sur le Cloud spécifié.
    """
    try:
        mongo_uri = build_mongo_uri(req)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erreur lors de la construction de l'URI de connexion : {str(e)}"
        )

    try:
        from app.scheduler.tasks import run_backup_job
        success = run_backup_job(
            db_name=req.db,
            collection_name=req.collection,
            provider=req.provider,
            dest_path=req.dest_path,
            mongo_uri=mongo_uri,
            provider_config=req.provider_config
        )
        if success:
            return {"status": "success", "message": f"Sauvegarde réussie vers {req.provider}."}
        else:
            raise HTTPException(
                status_code=500,
                detail="Le téléversement Cloud a échoué."
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution de la sauvegarde immédiate : {str(e)}"
        )


@router.get("/api/scheduler/status")
def get_scheduler_status():
    """
    Vérifie l'état actuel (actif ou non) du planificateur de tâches.
    """
    from app.scheduler.manager import scheduler_manager
    return {
        "status": "success",
        "running": scheduler_manager.is_running()
    }


@router.post("/api/scheduler/jobs")
def schedule_backup(req: ScheduleRequest):
    """
    Planifie ou met à jour une sauvegarde récurrente avec une expression cron.
    """
    try:
        # Validation rapide
        build_mongo_uri(req)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Paramètres MongoDB ou URI invalides : {str(e)}"
        )

    try:
        from app.scheduler.manager import scheduler_manager
        
        connection_details = None
        if not req.uri:
            connection_details = {
                "cluster": req.cluster,
                "username": req.username,
                "password": req.password
            }

        scheduler_manager.add_backup_job(
            job_id=req.job_id,
            cron_expression=req.cron_expression,
            db_name=req.db,
            collection_name=req.collection,
            provider=req.provider,
            dest_path=req.dest_path,
            mongo_uri=req.uri,
            connection_details=connection_details,
            provider_config=req.provider_config
        )
        return {
            "status": "success",
            "message": f"Tâche '{req.job_id}' planifiée avec succès."
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la planification de la tâche : {str(e)}"
        )


@router.get("/api/scheduler/jobs")
def get_scheduled_jobs():
    """
    Liste toutes les tâches récurrentes planifiées. Les informations d'authentification
    sensibles sont masquées.
    """
    from app.scheduler.manager import scheduler_manager
    try:
        jobs = scheduler_manager.list_jobs()
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des tâches : {str(e)}"
        )


@router.delete("/api/scheduler/jobs/{job_id}")
def delete_scheduled_job(job_id: str):
    """
    Supprime une tâche planifiée par son ID.
    """
    from app.scheduler.manager import scheduler_manager
    try:
        success = scheduler_manager.remove_backup_job(job_id)
        if success:
            return {
                "status": "success",
                "message": f"Tâche '{job_id}' supprimée avec succès."
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Tâche '{job_id}' introuvable."
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la suppression de la tâche : {str(e)}"
        )
