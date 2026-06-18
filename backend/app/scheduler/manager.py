import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from app.scheduler.tasks import run_backup_job

logger = logging.getLogger("app.scheduler.manager")

class SchedulerManager:
    """
    Gestionnaire centralisé du cycle de vie du planificateur APScheduler.
    """
    def __init__(self):
        self.scheduler = None

    def start(self):
        """
        Démarre le planificateur avec persistance SQLite.
        """
        if self.scheduler and self.scheduler.running:
            logger.warning("Le planificateur est déjà en cours d'exécution.")
            return

        logger.info("Initialisation du planificateur APScheduler...")
        
        # Persistance des jobs dans une base de données SQLite locale
        jobstores = {
            'default': SQLAlchemyJobStore(url='sqlite:///jobs.sqlite')
        }
        
        # Configuration avec tolérance de délai d'exécution et coalescing
        job_defaults = {
            'coalesce': True,
            'max_instances': 1
        }

        self.scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults)
        self.scheduler.start()
        logger.info("Planificateur APScheduler démarré avec succès.")

    def shutdown(self):
        """
        Arrête proprement le planificateur.
        """
        if self.scheduler and self.scheduler.running:
            logger.info("Arrêt du planificateur APScheduler...")
            self.scheduler.shutdown()
            logger.info("Planificateur APScheduler arrêté.")
        else:
            logger.warning("Le planificateur n'était pas démarré.")

    def is_running(self) -> bool:
        """
        Retourne True si le planificateur est actif.
        """
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
        """
        Planifie une nouvelle sauvegarde récurrente.
        """
        if not self.is_running():
            raise RuntimeError("Le planificateur de tâches n'est pas actif.")

        # Analyse de l'expression cron standard (ex: '0 2 * * *')
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
        except Exception as e:
            raise ValueError(f"Expression cron invalide '{cron_expression}': {str(e)}")

        # Supprimer le job existant s'il y a collision d'ID pour le mettre à jour
        if self.scheduler.get_job(job_id):
            logger.info(f"Mise à jour de la tâche existante '{job_id}'")
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
        logger.info(f"Tâche de sauvegarde planifiée: ID={job_id}, cron='{cron_expression}'")

    def remove_backup_job(self, job_id: str) -> bool:
        """
        Supprime une tâche planifiée par son identifiant.
        """
        if not self.is_running():
            raise RuntimeError("Le planificateur de tâches n'est pas actif.")

        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"Tâche planifiée supprimée: ID={job_id}")
            return True
        
        logger.warning(f"Tâche planifiée introuvable: ID={job_id}")
        return False

    def list_jobs(self) -> list:
        """
        Retourne la liste des tâches planifiées. Les credentials sensibles sont masqués.
        """
        if not self.is_running():
            return []

        jobs_list = []
        for job in self.scheduler.get_jobs():
            # Masquage des variables sensibles pour la sécurité
            safe_kwargs = {}
            for k, v in job.kwargs.items():
                if k in ("connection_details", "provider_config", "mongo_uri") and v:
                    safe_kwargs[k] = "[SÉCURISÉ]"
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

# Singleton pour l'application
scheduler_manager = SchedulerManager()
