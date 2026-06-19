# Documentation Technique - Fonctionnement & API du Backend

Ce document détaille le fonctionnement global de l'application, sa structure, le rôle de chaque composant, ainsi que la spécification complète des endpoints d'API avec les formats JSON d'entrée et de sortie pour préparer le développement du frontend React.

---

## 🏗️ 1. Architecture et Flux de Fonctionnement (Workflow)

L'application fonctionne selon deux modes principaux :
1. **Export à la demande** : L'utilisateur fournit les informations d'une collection MongoDB, le backend extrait les données, les normalise en CSV et renvoie le fichier directement en téléchargement.
2. **Sauvegarde automatisée (Planifiée/Directe sur le Cloud)** : Le backend extrait les données MongoDB en arrière-plan et les envoie sur un stockage cloud (S3, Drive, Dropbox).

### Schéma Global des Flux

```mermaid
graph TD
    %% Composants principaux
    subgraph Frontend (Futur React)
        UI[Interface React]
    end

    subgraph API Backend (FastAPI)
        R[Routes API]
        DB[Extracteur DB]
        PROC[Processeur CSV]
        SCHED[Planificateur APScheduler]
        CL_FAC[Factory Cloud]
    end

    subgraph Stockages Externes
        MONGO[(Bases MongoDB)]
        S3[AWS S3]
        GDRIVE[Google Drive]
        DROPBOX[Dropbox Space]
        SQLITE[(SQLite jobs.sqlite)]
    end

    %% Flux A: Export direct
    UI -->|POST /api/export-csv| R
    R -->|Extraction| DB
    DB -->|Documents bruts| MONGO
    MONGO -->|Documents bruts| DB
    DB -->|List[Dict]| PROC
    PROC -->|Génération bytes CSV| R
    R -->|Fichier CSV en flux| UI

    %% Flux B: Planification de tâches
    UI -->|POST /api/scheduler/jobs| R
    R -->|Enregistre / Planifie| SCHED
    SCHED -->|Persistance de la tâche| SQLITE

    %% Flux C: Déclenchement de tâche planifiée
    SCHED -->|Déclenche à intervalle Cron| DB
    DB -->|Extraction| MONGO
    MONGO -->|Documents bruts| DB
    DB -->|List[Dict]| PROC
    PROC -->|CSV bytes| CL_FAC
    CL_FAC -->|Uploader adapté| S3
    CL_FAC -->|Uploader adapté| GDRIVE
    CL_FAC -->|Uploader adapté| DROPBOX
```

---

## 📂 2. Structure et Rôles des Composants

Le dossier `/backend` est structuré comme suit :

```
backend/
├── app/
│   ├── cloud/               # Gestion des connexions et des uploads Cloud
│   │   ├── base.py          # Interface Uploader standard
│   │   ├── s3.py            # Upload vers AWS S3 (via boto3)
│   │   ├── gdrive.py        # Upload vers Google Drive
│   │   ├── dropbox.py       # Upload vers Dropbox (via dropbox SDK)
│   │   └── factory.py       # Choix et instanciation dynamique des uploaders
│   │
│   ├── scheduler/           # Planification en arrière-plan des tâches
│   │   ├── manager.py       # Initialisation d'APScheduler avec persistance SQLite
│   │   └── tasks.py         # Code de la tâche exécutée (run_backup_job)
│   │
│   ├── config.py            # Configuration globale et chargement de .env
│   ├── database.py          # Logique d'extraction de MongoDB (par lots)
│   ├── models.py            # Modèles de données Pydantic (validation JSON)
│   ├── processor.py         # Aplatissement JSON et conversion en bytes CSV
│   ├── routes.py            # Contrôleurs et aiguillage des requêtes HTTP
│   └── main.py              # Configuration globale FastAPI et gestion de cycle de vie (Lifespan)
│
├── tests/                   # Suite de tests automatisés (23 tests unitaires/intégration)
├── backup_cli.py            # Script CLI pour l'exécution manuelle hors-serveur
├── requirements.txt         # Dépendances Python du backend
├── main.py                  # Point d'entrée pour exécuter le serveur web
└── jobs.sqlite              # Base de données persistante contenant les tâches planifiées
```

---

## 🔌 3. Documentation des Endpoints d'API

Tous les endpoints acceptent et renvoient du contenu au format `application/json`, à l'exception de l'export direct qui retourne un flux binaire de fichier (`text/csv`).

---

### A. Export Direct CSV
* **URL** : `/api/export-csv` (accepte aussi `/export-csv`)
* **Méthode** : `POST`
* **Description** : Se connecte à MongoDB, normalise les données au format CSV et renvoie le fichier directement en téléchargement.

#### JSON Requis en Entrée (`ExportRequest`) :
```json
{
  "uri": "mongodb+srv://mon_user:mon_mot_de_passe@cluster0.mongodb.net/ma_db",
  "cluster": "cluster0",
  "username": "mon_user",
  "password": "mon_mot_de_passe",
  "db": "nom_de_la_base",
  "collection": "nom_de_la_collection"
}
```
> [!NOTE]
> Vous devez fournir **soit** la chaîne `"uri"` complète, **soit** le triplet (`"cluster"`, `"username"`, `"password"`). Les paramètres `"db"` et `"collection"` sont toujours requis.

#### Réponse en Sortie (Succès) :
* **Code HTTP** : `200 OK`
* **Content-Type** : `text/csv; charset=utf-8`
* **En-têtes** : `Content-Disposition: attachment; filename=nom_collection_export.csv`
* **Corps** : Données CSV brutes encodées en UTF-8 avec BOM (Byte Order Mark) pour compatibilité Excel.

#### Réponse en Sortie (Erreur, ex: Collection vide) :
* **Code HTTP** : `404 Not Found`
* **Corps JSON** :
```json
{
  "detail": "Aucun document trouvé dans la collection 'utilisateurs' de la base 'app_db'."
}
```

---

### B. Sauvegarde Immédiate sur le Cloud
* **URL** : `/api/backup`
* **Méthode** : `POST`
* **Description** : Déclenche immédiatement l'export et l'envoie sur le service Cloud spécifié.

#### JSON Requis en Entrée (`BackupRequest`) :
```json
{
  "uri": "mongodb://localhost:27017/",
  "db": "app_db",
  "collection": "utilisateurs",
  "provider": "s3",
  "dest_path": "backups/utilisateurs_backup_2026.csv",
  "provider_config": {
    "aws_access_key_id": "AKIA...",
    "aws_secret_access_key": "abc...",
    "region_name": "eu-west-3",
    "bucket_name": "nom-de-mon-bucket"
  }
}
```
* **`provider`** : `"s3"`, `"dropbox"`, `"gdrive"`, ou `"mock"` (écrit localement dans `mock_uploads/` sans identifiants réels).
* **`dest_path`** : Chemin de destination finale du fichier CSV dans le service cloud cible.
* **`provider_config`** : Optionnel. Si vide, utilise les variables définies dans le fichier `.env` du backend.

#### Réponse en Sortie (Succès) :
* **Code HTTP** : `200 OK`
* **Corps JSON** :
```json
{
  "status": "success",
  "message": "Sauvegarde réussie vers s3."
}
```

---

### C. État du Planificateur
* **URL** : `/api/scheduler/status`
* **Méthode** : `GET`
* **Description** : Indique si le moteur de planification des sauvegardes automatiques est démarré et actif.

#### Réponse en Sortie :
* **Code HTTP** : `200 OK`
* **Corps JSON** :
```json
{
  "status": "success",
  "running": true
}
```

---

### D. Planifier une Sauvegarde Récurrente (Cron)
* **URL** : `/api/scheduler/jobs`
* **Méthode** : `POST`
* **Description** : Crée ou met à jour une tâche programmée exécutée en arrière-plan. Elle sera stockée de façon permanente dans la base SQLite locale.

#### JSON Requis en Entrée (`ScheduleRequest`) :
```json
{
  "job_id": "sauvegarde_utilisateurs_nuit",
  "cron_expression": "0 2 * * *",
  "uri": "mongodb://localhost:27017/",
  "db": "app_db",
  "collection": "utilisateurs",
  "provider": "s3",
  "dest_path": "sauvegardes_auto/utilisateurs_daily.csv",
  "provider_config": {
    "bucket_name": "mon-bucket-s3"
  }
}
```
* **`job_id`** : Identifiant unique pour retrouver, modifier ou supprimer la tâche.
* **`cron_expression`** : Expression au format Cron standard (5 colonnes: `minute heure jour-du-mois mois jour-de-la-semaine`).
  * Exemples :
    * `"0 2 * * *"` : Tous les jours à 2h00 du matin.
    * `"*/30 * * * *"` : Toutes les 30 minutes (idéal pour les tests).

#### Réponse en Sortie (Succès) :
* **Code HTTP** : `200 OK`
* **Corps JSON** :
```json
{
  "status": "success",
  "message": "Tâche 'sauvegarde_utilisateurs_nuit' planifiée avec succès."
}
```

---

### E. Lister les Sauvegardes Planifiées actives
* **URL** : `/api/scheduler/jobs`
* **Méthode** : `GET`
* **Description** : Retourne la liste des tâches actives avec leur configuration et la date de leur prochaine exécution estimée.

#### Réponse en Sortie (Succès) :
* **Code HTTP** : `200 OK`
* **Corps JSON** :
```json
{
  "status": "success",
  "jobs": [
    {
      "id": "sauvegarde_utilisateurs_nuit",
      "next_run_time": "2026-06-20T02:00:00+02:00",
      "cron_expression": "cron[hour='2', minute='0']",
      "args": {
        "db_name": "app_db",
        "collection_name": "utilisateurs",
        "provider": "s3",
        "dest_path": "sauvegardes_auto/utilisateurs_daily.csv"
      },
      "kwargs": {
        "mongo_uri": "[SÉCURISÉ]",
        "connection_details": "[SÉCURISÉ]",
        "provider_config": "[SÉCURISÉ]"
      }
    }
  ]
}
```
> [!IMPORTANT]
> Par mesure de sécurité, toutes les variables sensibles comme les jetons d'accès ou les mots de passe de connexion MongoDB sont masquées et remplacées par la chaîne `"[SÉCURISÉ]"` dans la réponse JSON.

---

### F. Supprimer une Sauvegarde Planifiée
* **URL** : `/api/scheduler/jobs/{job_id}`
* **Méthode** : `DELETE`
* **Description** : Supprime définitivement une tâche récurrente de la planification et de la base persistante.

#### Paramètres :
* **`job_id`** (Dans l'URL) : Identifiant de la tâche à supprimer.

#### Réponse en Sortie (Succès) :
* **Code HTTP** : `200 OK`
* **Corps JSON** :
```json
{
  "status": "success",
  "message": "Tâche 'sauvegarde_utilisateurs_nuit' supprimée avec succès."
}
```

#### Réponse en Sortie (Si Tâche Introuvable) :
* **Code HTTP** : `404 Not Found`
* **Corps JSON** :
```json
{
  "detail": "Tâche 'job_inconnu' introuvable."
}
```
