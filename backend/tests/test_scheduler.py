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
    
    def test_start_already_running(self):
        """Test starting scheduler when already running"""
        self.manager.start()
        # Should not raise, just return
        self.manager.start()
        self.assertTrue(self.manager.is_running())
    
    def test_is_running_when_not_started(self):
        """Test is_running returns False when not started"""
        self.assertFalse(self.manager.is_running())
    
    def test_add_job_scheduler_not_running(self):
        """Test adding job when scheduler not running"""
        with self.assertRaises(SchedulerError):
            self.manager.add_backup_job(
                job_id="test_job",
                cron_expression="0 2 * * *",
                db_name="test_db",
                collection_name="test_coll",
                provider="mock",
                dest_path="test.csv"
            )
    
    def test_add_job_invalid_cron(self):
        """Test adding job with invalid cron expression"""
        self.manager.start()
        
        with self.assertRaises(SchedulerError):
            self.manager.add_backup_job(
                job_id="test_job",
                cron_expression="invalid cron",
                db_name="test_db",
                collection_name="test_coll",
                provider="mock",
                dest_path="test.csv"
            )
    
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
        
        # Verify job was added
        job = self.manager.scheduler.get_job("test_job")
        self.assertIsNotNone(job)
        self.assertEqual(job.id, "test_job")
    
    def test_remove_job_existing(self):
        """Test removing existing job"""
        self.manager.start()
        
        # Add job first
        self.manager.add_backup_job(
            job_id="test_job",
            cron_expression="0 2 * * *",
            db_name="test_db",
            collection_name="test_coll",
            provider="mock",
            dest_path="test.csv",
            mongo_uri="mongodb://localhost/"
        )
        
        # Remove it
        result = self.manager.remove_backup_job("test_job")
        self.assertTrue(result)
        self.assertIsNone(self.manager.scheduler.get_job("test_job"))
    
    def test_remove_job_non_existing(self):
        """Test removing non-existing job"""
        self.manager.start()
        
        result = self.manager.remove_backup_job("non_existent")
        self.assertFalse(result)
    
    def test_list_jobs_empty(self):
        """Test listing jobs when empty"""
        self.manager.start()
        
        jobs = self.manager.list_jobs()
        self.assertEqual(jobs, [])
    
    def test_list_jobs_with_jobs(self):
        """Test listing jobs with scheduled jobs"""
        self.manager.start()
        
        self.manager.add_backup_job(
            job_id="job1",
            cron_expression="0 2 * * *",
            db_name="db1",
            collection_name="coll1",
            provider="mock",
            dest_path="test1.csv",
            mongo_uri="mongodb://localhost/"
        )
        
        self.manager.add_backup_job(
            job_id="job2",
            cron_expression="0 3 * * *",
            db_name="db2",
            collection_name="coll2",
            provider="mock",
            dest_path="test2.csv"
        )
        
        jobs = self.manager.list_jobs()
        self.assertEqual(len(jobs), 2)


class TestRunBackupJob(unittest.TestCase):
    """Test run_backup_job function"""
    
    @patch('app.scheduler.tasks.BackupService')
    def test_run_backup_job_success_with_uri(self, mock_backup_service_class):
        """Test successful backup job with URI"""
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
            mongo_uri="mongodb://localhost:27017"
        )

        self.assertTrue(success)
        mock_fetch.assert_called_once_with("mongodb://localhost:27017", "test_db", "test_col")
        mock_get_uploader.assert_called_once_with("mock", None)
        mock_uploader.upload_file.assert_called_once()

    @patch("app.scheduler.manager.BackgroundScheduler")
    @patch("app.scheduler.manager.SQLAlchemyJobStore")
    def test_scheduler_manager_lifecycle(self, mock_jobstore, mock_bg_scheduler):
        # Mock du scheduler APScheduler
        mock_sched_instance = MagicMock()
        mock_bg_scheduler.return_value = mock_sched_instance
        mock_sched_instance.running = False
        
        manager = SchedulerManager()
        
        # Test démarrage
        manager.start()
        mock_sched_instance.start.assert_called_once()
        
        # Test is_running
        mock_sched_instance.running = True
        self.assertTrue(manager.is_running())
        
        # Mock d'ajout de tâche (le job n'existe pas encore)
        mock_sched_instance.get_job.return_value = None
        manager.add_backup_job(
            job_id="job1",
            cron_expression="*/5 * * * *",
            db_name="test_db",
            collection_name="test_col",
            provider="mock",
            dest_path="test.csv",
            mongo_uri="mongodb://localhost:27017"
        )
        mock_sched_instance.add_job.assert_called_once()
        
        # Mock de liste des tâches
        mock_job = MagicMock()
        mock_job.id = "job1"
        mock_job.next_run_time = None
        mock_job.trigger = "cron[minute='*/5']"
        mock_job.args = ["test_db", "test_col", "mock", "test.csv"]
        mock_job.kwargs = {"mongo_uri": "mongodb://localhost:27017"}
        
        mock_sched_instance.get_jobs.return_value = [mock_job]
        jobs = manager.list_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["id"], "job1")
        self.assertEqual(jobs[0]["kwargs"]["mongo_uri"], "[SÉCURISÉ]")
        
        # Mock de suppression de tâche (le job existe)
        mock_sched_instance.get_job.return_value = mock_job
        removed = manager.remove_backup_job("job1")
        self.assertTrue(removed)
        mock_sched_instance.remove_job.assert_called_once_with("job1")
        
        # Test shutdown
        manager.shutdown()
        mock_sched_instance.shutdown.assert_called_once()

if __name__ == "__main__":
    unittest.main()
