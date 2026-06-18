import unittest
from unittest.mock import patch, MagicMock
from app.scheduler.tasks import run_backup_job
from app.scheduler.manager import SchedulerManager

class TestScheduler(unittest.TestCase):
    @patch("app.scheduler.tasks.fetch_mongodb_documents")
    @patch("app.scheduler.tasks.get_uploader")
    def test_run_backup_job(self, mock_get_uploader, mock_fetch):
        # Configuration des mocks
        mock_fetch.return_value = [{"name": "test_doc", "value": 42}]
        mock_uploader = MagicMock()
        mock_get_uploader.return_value = mock_uploader
        mock_uploader.upload_file.return_value = True

        success = run_backup_job(
            db_name="test_db",
            collection_name="test_col",
            provider="mock",
            dest_path="backups/test.csv",
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
        
        # Mock d'ajout de tâche
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
        
        # Mock de suppression de tâche
        mock_sched_instance.get_job.return_value = mock_job
        removed = manager.remove_backup_job("job1")
        self.assertTrue(removed)
        mock_sched_instance.remove_job.assert_called_once_with("job1")
        
        # Test shutdown
        manager.shutdown()
        mock_sched_instance.shutdown.assert_called_once()

if __name__ == "__main__":
    unittest.main()
