"""Scheduler tasks"""

from app.core.logger import get_logger
from app.domain import BackupRequest
from app.services.backup_service import BackupService
from app.services.connection_service import ConnectionService

logger = get_logger(__name__)


def run_backup_job(
    db_name: str,
    collection_name: str,
    provider: str,
    dest_path: str,
    mongo_uri: str = None,
    connection_details: dict = None,
    provider_config: dict = None
) -> bool:
    """
    Scheduled task for running backups.
    
    Args:
        db_name: Database name
        collection_name: Collection name
        provider: Cloud provider
        dest_path: Destination path
        mongo_uri: MongoDB connection URI
        connection_details: Alternative connection details
        provider_config: Cloud provider configuration
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"Backup job started: {db_name}.{collection_name} -> {provider}")
    
    try:
        # Build request
        if mongo_uri:
            req = BackupRequest(
                uri=mongo_uri,
                db=db_name,
                collection=collection_name,
                provider=provider,
                dest_path=dest_path,
                provider_config=provider_config
            )
        else:
            req = BackupRequest(
                cluster=connection_details.get("cluster"),
                username=connection_details.get("username"),
                password=connection_details.get("password"),
                db=db_name,
                collection=collection_name,
                provider=provider,
                dest_path=dest_path,
                provider_config=provider_config
            )
        
        # Execute backup
        backup_service = BackupService()
        result = backup_service.backup_to_cloud(req)
        
        logger.info(f"Backup job completed successfully: {result}")
        return True
        
    except Exception as e:
        logger.error(f"Backup job failed: {str(e)}", exc_info=True)
        return False
