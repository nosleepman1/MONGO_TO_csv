import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch("app.routes.api.ExportService.export_to_csv")
    def test_export_csv_success(self, mock_export):
        """Test successful CSV export"""
        mock_export.return_value = (b"name,age\nAlice,30\n", "users_export.csv")
        
        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "users"
        }
        
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=users_export.csv", response.headers["content-disposition"])

    @patch("app.routes.api.ExportService.export_to_csv")
    def test_export_csv_empty_collection(self, mock_export):
        """Test export from empty collection"""
        from app.core.exceptions import EmptyCollectionError
        mock_export.side_effect = EmptyCollectionError("testdb", "empty")
        
        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "empty"
        }
        
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("No documents found", response.json()["detail"])

    @patch("app.routes.api.ExportService.export_to_csv")
    def test_export_csv_connection_error(self, mock_export):
        """Test export with MongoDB connection error"""
        from app.core.exceptions import MongoDBConnectionError
        mock_export.side_effect = MongoDBConnectionError("Connection failed")
        
        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "users"
        }
        
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Connection failed", response.json()["detail"])

    def test_export_csv_validation_error(self):
        """Test export with missing required fields"""
        payload = {
            "uri": "mongodb://localhost:27017/"
        }
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())

    @patch("app.routes.api.BackupService.backup_to_cloud")
    def test_backup_success(self, mock_backup):
        """Test successful backup"""
        mock_backup.return_value = {
            "status": "success",
            "message": "Backup successful to mock",
            "filename": "users_export.csv",
            "size_bytes": 1024
        }
        
        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "users",
            "provider": "mock",
            "dest_path": "backups/users.csv"
        }
        
        response = self.client.post("/api/backup", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

    def test_scheduler_status(self):
        """Test scheduler status endpoint"""
        response = self.client.get("/api/scheduler/status")
        self.assertEqual(response.status_code, 200)
        self.assertIn("running", response.json())

    def test_schedule_job_validation_error(self):
        """Test schedule job with missing fields"""
        payload = {
            "uri": "mongodb://localhost:27017/"
        }
        response = self.client.post("/api/scheduler/jobs", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_get_scheduled_jobs(self):
        """Test getting list of scheduled jobs"""
        response = self.client.get("/api/scheduler/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("jobs", response.json())


if __name__ == "__main__":
    unittest.main()
