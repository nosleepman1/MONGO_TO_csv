"""Tests for services"""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

from app.services.connection_service import ConnectionService
from app.services.export_service import ExportService
from app.services.backup_service import BackupService
from app.domain import ExportRequest, BackupRequest
from app.core.exceptions import ValidationError, EmptyCollectionError


class TestConnectionService(unittest.TestCase):
    """Test ConnectionService"""
    
    def test_build_uri_from_direct_uri(self):
        """Test building URI from direct connection string"""
        req = ExportRequest(
            uri="mongodb://localhost:27017/",
            db="test",
            collection="coll"
        )
        
        uri = ConnectionService.build_mongo_uri(req)
        self.assertEqual(uri, "mongodb://localhost:27017/")
    
    def test_build_uri_cluster_no_suffix(self):
        """Test building URI with cluster name (no .mongodb.net)"""
        req = ExportRequest(
            cluster="cluster0",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        
        uri = ConnectionService.build_mongo_uri(req)
        self.assertIn("cluster0.mongodb.net", uri)
        self.assertIn("mongodb+srv://", uri)
    
    def test_build_uri_cluster_with_one_dot(self):
        """Test building URI with cluster having one dot"""
        req = ExportRequest(
            cluster="cluster0.vvtqpfm",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        
        uri = ConnectionService.build_mongo_uri(req)
        self.assertIn("cluster0.vvtqpfm.mongodb.net", uri)
    
    def test_build_uri_complete_cluster(self):
        """Test building URI with complete cluster name"""
        req = ExportRequest(
            cluster="cluster0.vvtqpfm.mongodb.net",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        
        uri = ConnectionService.build_mongo_uri(req)
        self.assertIn("cluster0.vvtqpfm.mongodb.net", uri)
        # Should not duplicate .mongodb.net
        self.assertNotIn(".mongodb.net.mongodb.net", uri)
    
    def test_build_uri_url_encoding(self):
        """Test URI URL encoding for special characters"""
        req = ExportRequest(
            cluster="cluster0",
            username="user@example.com",
            password="pwd/with:special",
            db="test",
            collection="coll"
        )
        
        uri = ConnectionService.build_mongo_uri(req)
        self.assertIn("user%40example.com", uri)
        self.assertIn("pwd%2Fwith%3Aspecial", uri)
    
    def test_build_uri_missing_credentials(self):
        """Test error when credentials missing"""
        from app.domain import ExportRequest as ER
        # Pydantic will raise validation error immediately, not when we call build_mongo_uri
        with self.assertRaises(Exception):  # ValidationError or ValueError
            ER(db="test", collection="coll")


class TestExportService(unittest.TestCase):
    """Test ExportService"""
    
    @patch('app.services.export_service.MongoDBRepository')
    @patch('app.services.export_service.CSVProcessor')
    def test_export_to_csv_success(self, mock_processor_class, mock_repo_class):
        """Test successful CSV export"""
        # Mock repository
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.fetch_documents.return_value = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        
        # Mock processor
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        mock_processor.clean_data.return_value = df
        mock_processor.generate_csv_bytes.return_value = b"test,csv"
        mock_processor.sanitize_filename.return_value = "users_export.csv"
        
        service = ExportService(
            mongodb_repo=mock_repo,
            csv_processor=mock_processor
        )
        
        req = ExportRequest(
            uri="mongodb://localhost/",
            db="test",
            collection="users"
        )
        
        csv_bytes, filename = service.export_to_csv(req)
        
        self.assertEqual(csv_bytes, b"test,csv")
        self.assertEqual(filename, "users_export.csv")
        mock_repo.fetch_documents.assert_called_once()
    
    @patch('app.services.export_service.MongoDBRepository')
    def test_export_to_csv_empty_collection(self, mock_repo_class):
        """Test export from empty collection"""
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.fetch_documents.return_value = []
        
        service = ExportService(mongodb_repo=mock_repo)
        
        req = ExportRequest(
            uri="mongodb://localhost/",
            db="test",
            collection="users"
        )
        
        with self.assertRaises(EmptyCollectionError):
            service.export_to_csv(req)


class TestBackupService(unittest.TestCase):
    """Test BackupService"""
    
    @patch('app.services.backup_service.get_uploader')
    @patch('app.services.backup_service.ExportService')
    def test_backup_to_cloud_success(self, mock_export_class, mock_uploader_factory):
        """Test successful backup to cloud"""
        # Mock export service
        mock_export = MagicMock()
        mock_export_class.return_value = mock_export
        mock_export.export_to_csv.return_value = (b"csv data", "users_export.csv")
        
        # Mock uploader
        mock_uploader = MagicMock()
        mock_uploader_factory.return_value = mock_uploader
        mock_uploader.upload_file.return_value = True
        
        service = BackupService(export_service=mock_export)
        
        req = BackupRequest(
            uri="mongodb://localhost/",
            db="test",
            collection="users",
            provider="mock",
            dest_path="backups/users.csv"
        )
        
        result = service.backup_to_cloud(req)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("filename", result)
        self.assertIn("size_bytes", result)
        mock_export.export_to_csv.assert_called_once()
        mock_uploader.upload_file.assert_called_once_with(b"csv data", "backups/users.csv")


if __name__ == "__main__":
    unittest.main()
