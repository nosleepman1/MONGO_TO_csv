"""Backup service - Cloud backup orchestration"""

from app.core.logger import get_logger
from app.core.exceptions import CloudUploadError
from app.domain.models import BackupRequest
from app.services.connection_service import ConnectionService
from app.services.export_service import ExportService
from app.cloud.factory import get_uploader

logger = get_logger(__name__)


class BackupService:
    """Service for creating backups and uploading to cloud"""
    
    def __init__(
        self,
        export_service: ExportService = None,
        connection_service: ConnectionService = None
    ):
        """Initialize with dependencies"""
        self.export_service = export_service or ExportService()
        self.connection_service = connection_service or ConnectionService()
    
    def backup_to_cloud(self, req: BackupRequest) -> dict:
        """
        Creates backup and uploads to cloud provider.
        
        Args:
            req: BackupRequest with MongoDB and cloud details
            
        Returns:
            Status dictionary
            
        Raises:
            Various exceptions from services
        """
        logger.info(f"Starting backup: {req.db}.{req.collection} -> {req.provider}")
        
        try:
            # 1. Export to CSV
            csv_bytes, filename = self.export_service.export_to_csv(req)
            
            # 2. Get cloud uploader
            uploader = get_uploader(req.provider, req.provider_config)
            
            # 3. Upload to cloud
            success = uploader.upload_file(csv_bytes, req.dest_path)
            
            if not success:
                raise CloudUploadError(
                    req.provider,
                    "Upload returned False"
                )
            
            logger.info(f"Backup successful: {filename} to {req.provider}")
            return {
                "status": "success",
                "message": f"Backup successful to {req.provider}",
                "filename": filename,
                "size_bytes": len(csv_bytes)
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            raise
