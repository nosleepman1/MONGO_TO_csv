# API Endpoints - Documentation Complète

## 🌐 Endpoints Disponibles

### 1. GET `/` - Serve UI

Sert l'interface utilisateur web interactive.

**Réponse:**
- Status: `200 OK`
- Content-Type: `text/html`
- Body: HTML page

```bash
curl http://localhost:8000/
```

---

### 2. POST `/export-csv` - Export MongoDB vers CSV

Récupère tous les documents d'une collection MongoDB et les exporte en CSV propre.

**URL Alternatives:**
- `POST /api/export-csv` (alias)

**Request Body:**

```json
{
  "uri": "mongodb+srv://user:pass@cluster.mongodb.net/",
  "db": "mydb",
  "collection": "users"
}
```

**OU (alternative sans URI directe):**

```json
{
  "cluster": "cluster0",
  "username": "user",
  "password": "pass",
  "db": "mydb",
  "collection": "users"
}
```

**Réponse Succès (200 OK):**
- Content-Type: `text/csv; charset=utf-8`
- Content-Disposition: `attachment; filename=users_export.csv`
- Body: Contenu CSV avec BOM UTF-8

**Réponse Erreurs:**

| Status | Condition | Detail |
|--------|-----------|--------|
| 400 | Credentials invalides | "MongoDB authentication or connection failed" |
| 404 | Collection vide | "No documents found in collection..." |
| 422 | Validation Pydantic | Détails des champs manquants |

**Exemples:**

```bash
# Avec URI directe
curl -X POST http://localhost:8000/export-csv \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "mongodb://localhost:27017/",
    "db": "test",
    "collection": "products"
  }' \
  -o products.csv

# Avec credentials séparés
curl -X POST http://localhost:8000/export-csv \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": "cluster0.abc123",
    "username": "admin",
    "password": "secure123",
    "db": "production",
    "collection": "orders"
  }' \
  -o orders.csv
```

---

### 3. POST `/api/backup` - Sauvegarde Immédiate vers Cloud

Déclenche une sauvegarde instantanée d'une collection MongoDB vers un fournisseur cloud.

**Request Body:**

```json
{
  "uri": "mongodb+srv://user:pass@cluster.mongodb.net/",
  "db": "mydb",
  "collection": "users",
  "provider": "s3",
  "dest_path": "backups/users.csv",
  "provider_config": {
    "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "region_name": "eu-west-3",
    "bucket_name": "my-backup-bucket"
  }
}
```

**Fournisseurs Acceptés:**
- `s3` - Amazon S3
- `dropbox` - Dropbox
- `gdrive` - Google Drive
- `mock` - Local mock (développement)

**Réponse Succès (200 OK):**

```json
{
  "status": "success",
  "message": "Backup successful to s3",
  "filename": "users_export.csv",
  "size_bytes": 12345
}
```

**Réponse Erreurs:**

| Status | Condition |
|--------|-----------|
| 400 | Credentials MongoDB invalides |
| 404 | Collection vide |
| 500 | Erreur cloud upload |

**Exemples:**

```bash
# Backup vers S3
curl -X POST http://localhost:8000/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "mongodb://localhost:27017/",
    "db": "mydb",
    "collection": "users",
    "provider": "s3",
    "dest_path": "backups/users.csv",
    "provider_config": {
      "bucket_name": "my-bucket"
    }
  }'

# Backup vers Dropbox
curl -X POST http://localhost:8000/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": "cluster0",
    "username": "admin",
    "password": "pass",
    "db": "mydb",
    "collection": "orders",
    "provider": "dropbox",
    "dest_path": "/backups/orders.csv",
    "provider_config": {
      "access_token": "sl.Bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  }'

# Backup vers Google Drive
curl -X POST http://localhost:8000/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "mongodb://localhost:27017/",
    "db": "mydb",
    "collection": "customers",
    "provider": "gdrive",
    "dest_path": "customers.csv",
    "provider_config": {
      "credentials_file": "credentials.json",
      "folder_id": "1Bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
  }'

# Backup vers mock (développement)
curl -X POST http://localhost:8000/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "mongodb://localhost:27017/",
    "db": "test",
    "collection": "test_data",
    "provider": "mock",
    "dest_path": "test.csv"
  }'
```

---

### 4. GET `/api/scheduler/status` - État du Planificateur

Retourne l'état du planificateur de tâches APScheduler.

**Réponse:**

```json
{
  "status": "success",
  "running": true
}
```

**Exemple:**

```bash
curl http://localhost:8000/api/scheduler/status
```

---

### 5. POST `/api/scheduler/jobs` - Planifier une Sauvegarde

Planifie une sauvegarde récurrente avec une expression cron standard.

**Request Body:**

```json
{
  "job_id": "daily-users-backup",
  "cron_expression": "0 2 * * *",
  "uri": "mongodb://localhost:27017/",
  "db": "mydb",
  "collection": "users",
  "provider": "s3",
  "dest_path": "backups/daily/users.csv",
  "provider_config": {
    "bucket_name": "my-bucket"
  }
}
```

**Champs:**

| Field | Type | Requis | Description |
|-------|------|--------|-------------|
| job_id | string | ✓ | Identifiant unique pour la tâche |
| cron_expression | string | ✓ | Expression cron: `minute hour day month day_of_week` |
| uri | string | - | URI MongoDB (OU cluster+username+password) |
| cluster | string | - | Cluster Atlas (OU uri) |
| username | string | - | Username MongoDB (OU uri) |
| password | string | - | Password MongoDB (OU uri) |
| db | string | ✓ | Nom base de données |
| collection | string | ✓ | Nom collection |
| provider | string | ✓ | s3, dropbox, gdrive, mock |
| dest_path | string | ✓ | Chemin destination sur cloud |
| provider_config | object | - | Config spécifique au provider |

**Expressions Cron Courantes:**

| Expression | Signification |
|-----------|---------------|
| `0 2 * * *` | Tous les jours à 2h du matin |
| `0 */4 * * *` | Toutes les 4 heures |
| `0 9-17 * * MON-FRI` | 9h-17h en jours de semaine |
| `0 0 1 * *` | 1er du mois à minuit |
| `*/15 * * * *` | Tous les 15 minutes |
| `0 0 * * 0` | Chaque dimanche à minuit |

**Réponse Succès (200 OK):**

```json
{
  "status": "success",
  "message": "Job 'daily-users-backup' scheduled successfully"
}
```

**Réponse Erreurs:**

| Status | Condition |
|--------|-----------|
| 400 | Expression cron invalide |
| 500 | Scheduler non actif |

**Exemples:**

```bash
# Planifier backup quotidien à 2h
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "nightly-backup",
    "cron_expression": "0 2 * * *",
    "uri": "mongodb://localhost:27017/",
    "db": "mydb",
    "collection": "users",
    "provider": "s3",
    "dest_path": "backups/users.csv",
    "provider_config": {"bucket_name": "my-bucket"}
  }'

# Planifier backup 4 fois par jour
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "quarterly-backup",
    "cron_expression": "0 */6 * * *",
    "cluster": "cluster0",
    "username": "admin",
    "password": "secure",
    "db": "production",
    "collection": "orders",
    "provider": "dropbox",
    "dest_path": "/backups/orders.csv",
    "provider_config": {"access_token": "sl.Bxxxxx"}
  }'
```

---

### 6. GET `/api/scheduler/jobs` - Lister Tâches Planifiées

Retourne la liste de toutes les tâches planifiées (credentials masquées).

**Réponse:**

```json
{
  "status": "success",
  "jobs": [
    {
      "id": "daily-users-backup",
      "next_run_time": "2026-07-03T02:00:00+00:00",
      "cron_expression": "cron[month='*', day='*', day_of_week='*', hour='2', minute='0']",
      "args": {
        "db_name": "mydb",
        "collection_name": "users",
        "provider": "s3",
        "dest_path": "backups/users.csv"
      },
      "kwargs": {
        "mongo_uri": "[SECURED]",
        "connection_details": null,
        "provider_config": "[SECURED]"
      }
    }
  ]
}
```

**Exemple:**

```bash
curl http://localhost:8000/api/scheduler/jobs
```

---

## 🔐 Sécurité

### Credentials Sensibles

Les credentials MongoDB et cloud sont:
- **Jamais loggés** en clair
- **Masqués** quand listées via API (`[SECURED]`)
- **Acceptés** via JSON POST body
- **Optionnellement** stockés dans `.env`

### Best Practices

1. **Utilisez HTTPS** en production
2. **Stockez credentials** dans variables d'environnement ou `.env`
3. **Utilisez tokens IAM** plutôt que clés AWS longue vie
4. **Auditez logs** pour détection anomalies
5. **Rotate credentials** régulièrement

---

## ⚙️ Configuration

### Variables d'Environnement

```bash
# MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# AWS S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=eu-west-3
AWS_S3_BUCKET=my-backup-bucket

# Dropbox
DROPBOX_ACCESS_TOKEN=sl.Bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google Drive
GDRIVE_CREDENTIALS_FILE=credentials.json
GDRIVE_FOLDER_ID=1Bxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🚀 Démarrage

```bash
# Installation dépendances
pip install -r requirements.txt

# Démarrage serveur
cd backend
python main.py

# Serveur lancé sur http://localhost:8000
```

---

## 📊 Codes HTTP

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 400 | Erreur client (credentials, validation) |
| 404 | Collection/ressource non trouvée |
| 422 | Erreur validation Pydantic |
| 500 | Erreur serveur |

---

## 🧪 Tests

```bash
# Tous les tests
python -m unittest discover -s tests -p "test_*.py" -v

# Test spécifique
python -m unittest tests.test_routes.TestRoutes.test_export_csv_success
```

---

**Version:** 1.1.0  
**Status:** Production Ready  
**Dernière mise à jour:** 2026-07-02
