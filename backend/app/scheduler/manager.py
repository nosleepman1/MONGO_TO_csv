"""Scheduler manager - APScheduler lifecycle management"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from app.scheduler.tasks import run_backup_job
from app.core.logger import get_logger
from app.core.exceptions import SchedulerError

logger = get_logger(__name__)


class SchedulerManager:
    """Centralized scheduler lifecycle manager"""
    
    def __init__(self):
        self.scheduler = None

    def start(self):
        """Start the scheduler with SQLite persistence"""
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler already running")
            return

        try:
            logger.info("Starting APScheduler...")
            
            jobstores = {
                'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
            }
            
            job_defaults = {
                'coalesce': True,
                'max_instances': 1
            }

            self.scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults)
            self.scheduler.start()
            logger.info("APScheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            raise SchedulerError(f"Failed to start scheduler: {str(e)}")

    def shutdown(self):
        """Stop scheduler gracefully"""
        if self.scheduler and self.scheduler.running:
            logger.info("Stopping APScheduler...")
            self.scheduler.shutdown()
            logger.info("APScheduler stopped")
        else:
            logger.warning("Scheduler was not running")

    def is_running(self) -> bool:
        """Check if scheduler is active"""
        return self.scheduler is not None and self.scheduler.running

    def add_backup_job(
        self,
        job_id: str,
        cron_expression: str,
        db_name: str,
        collection_name: str,
        provider: str,
        dest_path: str,
        mongo_uri: str = None,
        connection_details: dict = None,
        provider_config: dict = None
    ):
        """Schedule a new backup job"""
        if not self.is_running():
            raise SchedulerError("Scheduler is not active")

        try:
            trigger = CronTrigger.from_crontab(cron_expression)
        except Exception as e:
            raise SchedulerError(f"Invalid cron expression '{cron_expression}': {str(e)}")

        if self.scheduler.get_job(job_id):
            logger.info(f"Updating existing job '{job_id}'")
            self.scheduler.remove_job(job_id)

        self.scheduler.add_job(
            run_backup_job,
            trigger=trigger,
            id=job_id,
            args=[db_name, collection_name, provider, dest_path],
            kwargs={
                "mongo_uri": mongo_uri,
                "connection_details": connection_details,
                "provider_config": provider_config
            },
            replace_existing=True
        )
        logger.info(f"Job scheduled: ID={job_id}, cron='{cron_expression}'")

    def remove_backup_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if not self.is_running():
            raise SchedulerError("Scheduler is not active")

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removed: ID={job_id}")
            return True
        
        logger.warning(f"Job not found: ID={job_id}")
        return False

    def list_jobs(self) -> list:
        """List all scheduled jobs with sensitive data masked"""
        if not self.is_running():
            return []

        jobs_list = []
        for job in self.scheduler.get_jobs():
            safe_kwargs = {}
            for k, v in job.kwargs.items():
                if k in ("connection_details", "provider_config", "mongo_uri") and v:
                    safe_kwargs[k] = "[SECURED]"
                else:
                    safe_kwargs[k] = v

            jobs_list.append({
                "id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "cron_expression": str(job.trigger),
                "args": {
                    "db_name": job.args[0] if len(job.args) > 0 else None,
                    "collection_name": job.args[1] if len(job.args) > 1 else None,
                    "provider": job.args[2] if len(job.args) > 2 else None,
                    "dest_path": job.args[3] if len(job.args) > 3 else None,
                },
                "kwargs": safe_kwargs
            })
        return jobs_list


# Singleton instance
scheduler_manager = SchedulerManager()
