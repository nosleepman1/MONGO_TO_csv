"""Domain models - Pydantic models for data validation"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator


class ExportRequest(BaseModel):
    """Request model for MongoDB export to CSV"""
    
    uri: Optional[str] = Field(None, description="Direct MongoDB connection URI")
    cluster: Optional[str] = Field(None, description="Cluster name (Atlas)")
    username: Optional[str] = Field(None, description="MongoDB username")
    password: Optional[str] = Field(None, description="MongoDB password")
    db: str = Field(..., min_length=1, description="Database name")
    collection: str = Field(..., min_length=1, description="Collection name")
    
    @model_validator(mode="before")
    @classmethod
    def strip_whitespace(cls, values):
        """Strip whitespace from string fields"""
        if isinstance(values, dict):
            for field in ['uri', 'cluster', 'username', 'password', 'db', 'collection']:
                if field in values and isinstance(values[field], str):
                    values[field] = values[field].strip()
        return values
    
    @model_validator(mode="after")
    def check_credentials(self) -> "ExportRequest":
        """Validate that credentials are provided either as URI or cluster details"""
        if not self.uri:
            if not all([self.cluster, self.username, self.password]):
                raise ValueError(
                    "Provide either 'uri' or all of (cluster, username, password)"
                )
        return self


class BackupRequest(ExportRequest):
    """Request model for MongoDB backup to cloud"""
    
    provider: str = Field(
        "mock",
        description="Cloud provider: s3, dropbox, gdrive, mock"
    )
    dest_path: str = Field(
        ...,
        min_length=1,
        description="Destination path on cloud"
    )
    provider_config: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Provider-specific configuration (tokens, bucket names, etc.)"
    )


class ScheduleRequest(BackupRequest):
    """Request model for scheduling backups"""
    
    job_id: str = Field(
        ...,
        min_length=1,
        description="Unique identifier for the scheduled job"
    )
    cron_expression: str = Field(
        ...,
        min_length=1,
        description="Standard cron expression (e.g., '0 2 * * *')"
    )
