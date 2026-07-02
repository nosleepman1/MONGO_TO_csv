"""Repository layer - MongoDB data access"""

from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from app.core.logger import get_logger
from app.core.exceptions import MongoDBConnectionError, MongoDBOperationError

logger = get_logger(__name__)


class MongoDBRepository:
    """Repository for MongoDB operations"""
    
    @staticmethod
    def fetch_documents(
        mongo_uri: str,
        db_name: str,
        collection_name: str,
        batch_size: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Fetches all documents from a MongoDB collection.
        
        Args:
            mongo_uri: Connection URI
            db_name: Database name
            collection_name: Collection name
            batch_size: Batch size for fetching
            
        Returns:
            List of documents
            
        Raises:
            MongoDBConnectionError: Connection or auth error
            MongoDBOperationError: Query error
        """
        client = None
        try:
            logger.info(f"Connecting to MongoDB: {db_name}.{collection_name}")
            
            # serverSelectionTimeoutMS: 5 seconds
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            
            # Verify connection with ping
            client.admin.command('ping')
            logger.info("MongoDB connection successful")
            
            db = client[db_name]
            collection = db[collection_name]
            
            # Fetch documents by batches
            cursor = collection.find().batch_size(batch_size)
            docs = list(cursor)
            
            logger.info(f"Fetched {len(docs)} documents from {collection_name}")
            return docs
            
        except (ConnectionFailure, OperationFailure) as e:
            msg = f"MongoDB authentication or connection failed: {str(e)}"
            logger.error(msg)
            raise MongoDBConnectionError(msg)
        except Exception as e:
            msg = f"MongoDB operation error: {str(e)}"
            logger.error(msg)
            raise MongoDBOperationError(msg)
        finally:
            if client:
                client.close()
                logger.debug("MongoDB connection closed")
