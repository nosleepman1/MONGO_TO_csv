# Architecture Future - Sauvegardes Automatisées & Exports Cloud

Ce document présente l'architecture cible du backend pour l'automatisation des sauvegardes MongoDB vers des services cloud (Amazon S3, Google Drive, Dropbox).

---

## 🏗️ Architecture Globale & Flux de Données

Le schéma ci-dessous illustre le flux de données allant de l'extraction de MongoDB à la sauvegarde finale dans le Cloud, orchestré par un planificateur.

```mermaid
graph TD
    A[MongoDB Database] -->|1. Extraction des Collections| B(Database Extractor)
    B -->|2. Documents Bruts| C(Data Processor)
    C -->|3. Normalisation & Conversion CSV| D[CSV Buffer in Memory / Temp File]
    
    E(Task Scheduler / Cron Job) -->|Déclenche l'export| B
    
    D -->|4. Upload du fichier| F{Cloud Storage Manager}
    F -->|Option A: AWS S3| G[Amazon S3 Bucket]
    F -->|Option B: Google Drive| H[Google Drive Folder]
    F -->|Option C: Dropbox| I[Dropbox Space]
    
    F -->|5. Journalisation| J[Logs & Monitoring]
```

---

## 📂 Structure du Répertoire Backend Cible

Pour intégrer ces nouvelles fonctionnalités, la structure du backend évoluera de la manière suivante :

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Démarrage de l'API FastAPI
│   ├── config.py            # Configuration (Clés API, Variables d'env)
│   ├── database.py          # Extraction MongoDB (avec pagination/streaming)
│   ├── models.py            # Modèles Pydantic de configuration d'export
│   ├── processor.py         # Normalisation des données et conversion en CSV
│   ├── routes.py            # Points d'accès de configuration
│   │
│   ├── scheduler/           # NOUVEAU: Orchestration des tâches
│   │   ├── __init__.py
│   │   ├── manager.py       # Gestion des tâches (APScheduler / Celery)
│   │   └── tasks.py         # Définition de la tâche de sauvegarde
│   │
│   └── cloud/               # NOUVEAU: Modules d'intégration Cloud
│       ├── __init__.py
│       ├── base.py          # Interface commune d'upload (UploaderInterface)
│       ├── s3.py            # Intégration AWS S3 (boto3)
│       ├── gdrive.py        # Intégration Google Drive (google-api-python-client)
│       └── dropbox.py       # Intégration Dropbox (dropbox SDK)
│
├── tests/                   # Suite de tests unitaires et d'intégration
├── requirements.txt         # Dépendances (ajout de boto3, google-api-client, apscheduler, etc.)
└── main.py                  # Point d'entrée de l'application
```

---

## ⚙️ Description des Nouveaux Composants Backend

### 1. Composant Extraction MongoDB (`app/database.py`)
Pour des sauvegardes automatiques de collections volumineuses, charger tous les documents en mémoire (via `list(collection.find())`) peut saturer le serveur (OOM). 
- **Évolution** : Utilisation de curseurs paginés ou de flux d'écriture temporaires (`tempfile`) pour écrire les lots (batches) de documents directement dans le fichier CSV au fur et à mesure.

### 2. Composant Planification (`app/scheduler/`)
Ce module gère le déclenchement des tâches de sauvegarde à des moments précis (ex: chaque nuit à 2h00).
- **Moteur recommandé** : **APScheduler** (Advanced Python Scheduler). Il s'intègre parfaitement à FastAPI et permet de planifier des tâches en arrière-plan sans dépendance externe lourde (comme Redis/RabbitMQ requis par Celery).
- **Stockage des tâches** : Un magasin persistant (comme SQLite via SQLAlchemy) pour conserver les tâches même après un redémarrage du serveur.

### 3. Composant Transfert Cloud (`app/cloud/`)
Pour garantir l'extensibilité, nous utilisons le principe de programmation par interface (polymorphisme) :

#### Interface Commune (`app/cloud/base.py`) :
```python
from abc import ABC, abstractmethod

class CloudUploader(ABC):
    @abstractmethod
    def upload_file(self, file_content: bytes, destination_path: str) -> bool:
        """Méthode universelle d'upload de fichier"""
        pass
```

#### Services Implémentés :
- **AWS S3 (`app/cloud/s3.py`)** : Utilise la bibliothèque `boto3`. Requiert un `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, et un `BUCKET_NAME`.
- **Google Drive (`app/cloud/gdrive.py`)** : Utilise `google-api-python-client`. Requiert un compte de service GCP ou un jeton OAuth2 rafraîchissable, ainsi qu'un identifiant de dossier cible (`FOLDER_ID`).
- **Dropbox (`app/cloud/dropbox.py`)** : Utilise le SDK `dropbox`. Requiert un jeton d'accès à l'API Dropbox.

---

## 🔒 Sécurité et Gestion des Secrets
Les identifiants de bases de données, jetons de stockage Cloud et clés d'API ne doivent jamais être stockés en clair.
- **Approche** : Utilisation d'un fichier `.env` lu par `app/config.py` à l'aide de `pydantic-settings`.
- **Exemple de configuration** :
  ```env
  MONGO_URI=mongodb+srv://...
  # Configuration AWS S3
  AWS_S3_KEY=AKIAIOSFODNN7EXAMPLE
  AWS_S3_SECRET=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
  AWS_S3_BUCKET=my-mongo-backups
  # Planification
  BACKUP_CRON_HOUR=2  # Tous les jours à 2h du matin
  ```
