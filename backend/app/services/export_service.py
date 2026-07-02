"""Export service - CSV export orchestration"""

from app.core.logger import get_logger
from app.core.exceptions import EmptyCollectionError
from app.domain.models import ExportRequest
from app.services.connection_service import ConnectionService
from app.repositories import MongoDBRepository
from app.processor import CSVProcessor

logger = get_logger(__name__)


class ExportService:
    """Service for exporting MongoDB collections to CSV"""
    
    def __init__(
        self,
        connection_service: ConnectionService = None,
        mongodb_repo: MongoDBRepository = None,
        csv_processor: CSVProcessor = None
    ):
        """Initialize with dependencies (allows testing with mocks)"""
        self.connection_service = connection_service or ConnectionService()
        self.mongodb_repo = mongodb_repo or MongoDBRepository()
        self.csv_processor = csv_processor or CSVProcessor()
    
    def export_to_csv(self, req: ExportRequest) -> tuple[bytes, str]:
        """
        Exports MongoDB collection to CSV.
        
        Args:
            req: ExportRequest with MongoDB and collection details
            
        Returns:
            Tuple of (csv_bytes, filename)
            
        Raises:
            Various exceptions from services/repositories
        """
        logger.info(f"Starting export: {req.db}.{req.collection}")
        
        # 1. Build connection URI
        mongo_uri = self.connection_service.build_mongo_uri(req)
        
        # 2. Fetch documents from MongoDB
        docs = self.mongodb_repo.fetch_documents(
            mongo_uri, req.db, req.collection
        )
        
        # 3. Check if collection has documents
        if not docs:
            raise EmptyCollectionError(req.db, req.collection)
        
        # 4. Clean data and generate CSV
        df = self.csv_processor.clean_data(docs)
        csv_bytes = self.csv_processor.generate_csv_bytes(df)
        
        # 5. Generate sanitized filename
        raw_filename = f"{req.collection}_export.csv"
        filename = self.csv_processor.sanitize_filename(raw_filename)
        
        logger.info(f"Export successful: {len(docs)} documents, {len(csv_bytes)} bytes")
        return csv_bytes, filename
