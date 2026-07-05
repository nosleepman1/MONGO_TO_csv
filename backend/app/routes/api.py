"""API routes - HTTP endpoints"""

import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from app.config import INDEX_HTML_PATH
from app.domain import ExportRequest, BackupRequest, ScheduleRequest
from app.services.export_service import ExportService
from app.services.backup_service import BackupService
from app.services.connection_service import ConnectionService
from app.core.exceptions import ApplicationError
from app.core.logger import get_logger

logger = get_logger(__name__)

# Initialize services
connection_service = ConnectionService()
export_service = ExportService(connection_service=connection_service)
backup_service = BackupService(connection_service=connection_service, export_service=export_service)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def read_root():
    """Serves the web UI or a status page fallback"""
    import os
    try:
        if os.path.exists(INDEX_HTML_PATH):
            with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        else:
            fallback_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>MongoDB to CSV Exporter API</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 2rem; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
                    .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); max-width: 600px; width: 100%; }
                    h1 { color: #2563eb; margin-top: 0; }
                    code { background: #e5e7eb; padding: 0.2rem 0.4rem; border-radius: 4px; font-family: monospace; }
                    pre { background: #1f2937; color: #f9fafb; padding: 1rem; border-radius: 6px; overflow-x: auto; }
                    .endpoints { list-style: none; padding: 0; }
                    .endpoints li { margin-bottom: 0.5rem; }
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>🟢 MongoDB to CSV Exporter API</h1>
                    <p>Le serveur backend FastAPI est actif et opérationnel.</p>
                    <p>L'interface utilisateur React n'est pas encore buildée (<code>frontend/dist/index.html</code> introuvable). Pour l'utiliser en développement, lancez :</p>
                    <pre>cd frontend
npm install
npm run dev</pre>
                    <h3>Endpoints disponibles :</h3>
                    <ul class="endpoints">
                        <li>👉 <code>POST /export-csv</code> - Exporter MongoDB vers CSV</li>
                        <li>👉 <code>POST /api/backup</code> - Lancer une sauvegarde Cloud immédiate</li>
                        <li>👉 <code>GET /api/scheduler/status</code> - Statut du planificateur</li>
                        <li>👉 <code>GET /api/scheduler/jobs</code> - Lister les jobs planifiés</li>
                        <li>👉 <code>DELETE /api/scheduler/jobs/{job_id}</code> - Supprimer un job</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=fallback_html)
    except Exception as e:
        logger.error(f"Error loading UI: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error loading UI: {str(e)}"
        )


@router.post("/export-csv")
@router.post("/api/export-csv")
def export_csv(req: ExportRequest):
    """
    Exports MongoDB collection to CSV.
    
    Args:
        req: ExportRequest with MongoDB details
        
    Returns:
        CSV file as attachment
    """
    try:
        csv_bytes, filename = export_service.export_to_csv(req)
        
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except ApplicationError as e:
        logger.warning(f"Export error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in export: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/backup")
def run_backup(req: BackupRequest):
    """
    Triggers immediate backup to cloud.
    
    Args:
        req: BackupRequest with MongoDB and cloud details
        
    Returns:
        Status JSON
    """
    try:
        result = backup_service.backup_to_cloud(req)
        return result
    except ApplicationError as e:
        logger.warning(f"Backup error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in backup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/scheduler/status")
def get_scheduler_status():
    """Get scheduler status"""
    try:
        from app.scheduler.manager import scheduler_manager
        return {
            "status": "success",
            "running": scheduler_manager.is_running()
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/scheduler/jobs")
def schedule_backup(req: ScheduleRequest):
    """
    Schedules a recurring backup with cron expression.
    
    Args:
        req: ScheduleRequest with all details
        
    Returns:
        Status JSON
    """
    try:
        from app.scheduler.manager import scheduler_manager
        
        # Validate connection
        connection_service.build_mongo_uri(req)
        
        # Schedule job
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
            "message": f"Job '{req.job_id}' scheduled successfully"
        }
    except ApplicationError as e:
        logger.warning(f"Scheduler error: {e.message}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/scheduler/jobs")
def get_scheduled_jobs():
    """Get list of scheduled jobs"""
    try:
        from app.scheduler.manager import scheduler_manager
        jobs = scheduler_manager.list_jobs()
        return {"status": "success", "jobs": jobs}
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/scheduler/jobs/{job_id}")
def delete_scheduled_job(job_id: str):
    """Delete a scheduled job"""
    try:
        from app.scheduler.manager import scheduler_manager
        success = scheduler_manager.remove_backup_job(job_id)
        if success:
            return {
                "status": "success",
                "message": f"Job '{job_id}' deleted successfully"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    except Exception as e:
        logger.error(f"Error deleting job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
