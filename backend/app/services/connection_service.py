"""Service layer - Business logic orchestration"""

import urllib.parse
from typing import Optional, Dict, Any
from app.core.logger import get_logger
from app.core.exceptions import ValidationError
from app.domain.models import ExportRequest, BackupRequest

logger = get_logger(__name__)


class ConnectionService:
    """Service for handling MongoDB connection details"""
    
    @staticmethod
    def build_mongo_uri(req: ExportRequest) -> str:
        """
        Builds MongoDB URI from request details.
        
        Handles:
        - Direct URI if provided
        - Cluster/username/password combination
        - MongoDB Atlas suffix correction (.mongodb.net)
        
        Args:
            req: ExportRequest with connection details
            
        Returns:
            MongoDB connection URI
            
        Raises:
            ValidationError: Invalid credentials
        """
        try:
            if req.uri:
                logger.debug("Using provided URI")
                return req.uri
            
            if not req.cluster or not req.username or not req.password:
                raise ValidationError(
                    "Provide either URI or (cluster, username, password)"
                )
            
            # Fix Atlas hostname
            cluster_host = req.cluster
            if not cluster_host.endswith(".mongodb.net"):
                parts = cluster_host.split('.')
                if len(parts) <= 2:
                    cluster_host = f"{cluster_host}.mongodb.net"
            
            # URL encode credentials
            enc_user = urllib.parse.quote_plus(req.username)
            enc_pwd = urllib.parse.quote_plus(req.password)
            uri = f"mongodb+srv://{enc_user}:{enc_pwd}@{cluster_host}/"
            
            logger.debug("Built MongoDB URI")
            return uri
            
        except Exception as e:
            msg = f"Error building MongoDB URI: {str(e)}"
            logger.error(msg)
            raise ValidationError(msg)
