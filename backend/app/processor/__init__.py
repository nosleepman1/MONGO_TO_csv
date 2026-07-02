"""CSV processing module"""

import io
import re
from typing import List, Dict, Any
import pandas as pd
from app.core.logger import get_logger
from app.core.exceptions import CSVGenerationError

logger = get_logger(__name__)


class CSVProcessor:
    """Handles CSV processing and generation"""
    
    @staticmethod
    def clean_data(docs: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Normalizes MongoDB documents to clean DataFrame:
        - Excludes '_id' column
        - Flattens nested structures (e.g., user.name)
        - Converts lists to comma-separated strings
        
        Args:
            docs: List of MongoDB documents
            
        Returns:
            Cleaned pandas DataFrame
        """
        if not docs:
            logger.warning("No documents to clean")
            return pd.DataFrame()
        
        try:
            # Normalize nested structures
            df = pd.json_normalize(docs)
            
            # Exclude _id if present
            if "_id" in df.columns:
                df = df.drop(columns=["_id"])
            
            # Convert lists to comma-separated strings
            for col in df.columns:
                if df[col].apply(lambda x: isinstance(x, list)).any():
                    df[col] = df[col].apply(
                        lambda x: ", ".join(map(str, x)) if isinstance(x, list) else x
                    )
            
            logger.info(f"Cleaned data: {df.shape[0]} rows, {df.shape[1]} columns")
            return df
            
        except Exception as e:
            msg = f"Error cleaning data: {str(e)}"
            logger.error(msg)
            raise CSVGenerationError(msg)
    
    @staticmethod
    def generate_csv_bytes(df: pd.DataFrame) -> bytes:
        """
        Generates CSV content as bytes with UTF-8-SIG encoding (BOM).
        
        Args:
            df: Pandas DataFrame
            
        Returns:
            CSV content as bytes
        """
        try:
            stream = io.StringIO()
            df.to_csv(stream, index=False)
            csv_text = stream.getvalue()
            csv_bytes = csv_text.encode("utf-8-sig")
            
            logger.info(f"Generated CSV: {len(csv_bytes)} bytes")
            return csv_bytes
            
        except Exception as e:
            msg = f"Error generating CSV: {str(e)}"
            logger.error(msg)
            raise CSVGenerationError(msg)
    
    @staticmethod
    def sanitize_filename(name: str) -> str:
        """
        Sanitizes filename for safe download.
        
        Args:
            name: Original filename
            
        Returns:
            Sanitized filename
        """
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", name)
        return sanitized
