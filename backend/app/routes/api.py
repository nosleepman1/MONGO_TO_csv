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
    """Serves the web UI"""
    try:
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
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
