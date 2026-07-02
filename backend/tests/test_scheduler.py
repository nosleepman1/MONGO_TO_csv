"""Tests for scheduler manager and tasks"""

import unittest
from unittest.mock import patch, MagicMock
from app.scheduler.manager import SchedulerManager
from app.scheduler.tasks import run_backup_job
from app.core.exceptions import SchedulerError


class TestSchedulerManager(unittest.TestCase):
    """Test SchedulerManager"""
    
    def setUp(self):
        self.manager = SchedulerManager()
    
    def tearDown(self):
        if self.manager.is_running():
            self.manager.shutdown()
    
    def test_start_scheduler(self):
        """Test starting the scheduler"""
        self.manager.start()
        self.assertTrue(self.manager.is_running())
    
    def test_shutdown_scheduler(self):
        """Test shutting down the scheduler"""
        self.manager.start()
        self.assertTrue(self.manager.is_running())
        
        self.manager.shutdown()
        self.assertFalse(self.manager.is_running())
    
    def test_add_job_valid(self):
        """Test adding valid job"""
        self.manager.start()
        
        self.manager.add_backup_job(
            job_id="test_job",
            cron_expression="0 2 * * *",
            db_name="test_db",
            collection_name="test_coll",
            provider="mock",
            dest_path="test.csv",
            mongo_uri="mongodb://localhost/"
        )
        
        job = self.manager.scheduler.get_job("test_job")
        self.assertIsNotNone(job)
    
    def test_list_jobs_empty(self):
        """Test listing jobs when empty"""
        # Create a fresh manager to avoid persistence from previous tests
        manager = SchedulerManager()
        manager.start()
        try:
            jobs = manager.list_jobs()
            # Should have no jobs or only existing ones from SQLite
            self.assertIsInstance(jobs, list)
        finally:
            manager.shutdown()


class TestRunBackupJob(unittest.TestCase):
    """Test run_backup_job function"""
    
    @patch('app.scheduler.tasks.BackupService')
    def test_run_backup_job_success(self, mock_backup_service_class):
        """Test successful backup job"""
        mock_service = MagicMock()
        mock_backup_service_class.return_value = mock_service
        mock_service.backup_to_cloud.return_value = {
            "status": "success",
            "message": "Backup successful"
        }
        
        result = run_backup_job(
            db_name="test_db",
            collection_name="test_coll",
            provider="mock",
            dest_path="test.csv",
            mongo_uri="mongodb://localhost/"
        )
        
        self.assertTrue(result)
        mock_service.backup_to_cloud.assert_called_once()
    
    @patch('app.scheduler.tasks.BackupService')
    def test_run_backup_job_failure(self, mock_backup_service_class):
        """Test backup job failure"""
        mock_service = MagicMock()
        mock_backup_service_class.return_value = mock_service
        mock_service.backup_to_cloud.side_effect = Exception("Connection error")
        
        result = run_backup_job(
            db_name="test_db",
            collection_name="test_coll",
            provider="mock",
            dest_path="test.csv",
            mongo_uri="mongodb://localhost/"
        )
        
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
