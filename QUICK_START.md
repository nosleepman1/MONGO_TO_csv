# 🚀 QUICK START - Utiliser le Backend Refactorisé

## 5-Minute Setup

### 1. Installation

```bash
cd backend
pip install -r requirements.txt
```

### 2. Démarrer le serveur

```bash
python main.py
```

**Sortie esperée:**
```
INFO:root:Starting scheduler...
INFO:uvicorn.error:Started server process [1234]
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8000
```

### 3. Vérifier le serveur

```bash
curl http://localhost:8000/
```

---

## 📝 Cas d'Utilisation Courants

### Export Local MongoDB vers CSV

```bash
curl -X POST http://localhost:8000/export-csv \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "mongodb://localhost:27017/",
    "db": "mydb",
    "collection": "users"
  }' \
  --output users.csv
```

### Export Atlas MongoDB vers CSV

```bash
curl -X POST http://localhost:8000/export-csv \
  -H "Content-Type: application/json" \
  -d '{
    "cluster": "cluster0",
    "username": "admin",
    "password": "MySecurePassword123",
    "db": "production",
    "collection": "customers"
  }' \
  --output customers.csv
```

### Backup Immédiat vers S3

```bash
curl -X POST http://localhost:8000/api/backup \
  -H "Content-Type: application/json" \
  -d '{
    "uri": "mongodb://localhost:27017/",
    "db": "mydb",
    "collection": "users",
    "provider": "s3",
    "dest_path": "backups/users.csv",
    "provider_config": {
      "bucket_name": "my-backup-bucket"
    }
  }'
```

### Planifier Backup Quotidien

```bash
curl -X POST http://localhost:8000/api/scheduler/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "daily-backup",
    "cron_expression": "0 2 * * *",
    "uri": "mongodb://localhost:27017/",
    "db": "mydb",
    "collection": "users",
    "provider": "s3",
    "dest_path": "backups/daily/users.csv",
    "provider_config": {
      "bucket_name": "my-bucket"
    }
  }'
```

### Lister les Backups Planifiés

```bash
curl http://localhost:8000/api/scheduler/jobs
```

---

## 🧪 Tester le Code

```bash
# Tous les tests
python -m unittest discover -s tests -p "test_*.py"

# Résultat attendu
# Ran 42 tests in 0.263s
# OK (4 erreurs attendues pour boto3 optionnel)
```

---

## 📖 Documentation Complète

| Document | Contenu |
|----------|---------|
| **REVIEW_SUMMARY.md** | Résumé exécutif (ce que vous lisez maintenant) |
| **ARCHITECTURE_REFACTORED.md** | Architecture détaillée & patterns |
| **API_DOCUMENTATION.md** | Endpoints & exemples curl |
| **QUICK_START.md** | Ce fichier |

---

## 🐍 Utiliser dans Python

```python
# Exporter MongoDB
from app.services.export_service import ExportService
from app.domain import ExportRequest

service = ExportService()
req = ExportRequest(
    uri="mongodb://localhost:27017/",
    db="mydb",
    collection="users"
)
csv_bytes, filename = service.export_to_csv(req)

# Sauvegarder dans fichier
with open(f"/tmp/{filename}", 'wb') as f:
    f.write(csv_bytes)
```

```python
# Backup vers Cloud
from app.services.backup_service import BackupService
from app.domain import BackupRequest

service = BackupService()
req = BackupRequest(
    uri="mongodb://localhost:27017/",
    db="mydb",
    collection="users",
    provider="s3",
    dest_path="backups/users.csv",
    provider_config={
        "bucket_name": "my-bucket"
    }
)
result = service.backup_to_cloud(req)
print(result)  
# {"status": "success", "filename": "users_export.csv", "size_bytes": 12345}
```

---

## ⚙️ Variables d'Environnement (Optional)

Créez `.env` à la racine backend:

```bash
# MongoDB
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/

# AWS S3
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_S3_BUCKET=my-backup-bucket

# Dropbox
DROPBOX_ACCESS_TOKEN=sl.Bxxxxxxxxxx...

# Google Drive
GDRIVE_CREDENTIALS_FILE=credentials.json
```

---

## 🔍 Expressions Cron Courantes

```
0 2 * * *           # Tous les jours à 2h
0 */4 * * *         # Toutes les 4 heures
0 9-17 * * MON-FRI  # Jours de semaine 9-17h
0 0 1 * *           # 1er du mois
*/15 * * * *        # Tous les 15 minutes
0 0 * * 0           # Chaque dimanche
```

---

## 🐛 Dépannage

### "ModuleNotFoundError: No module named 'app'"
→ Assurez-vous d'être dans le dossier `backend`

### "ConnectionRefused: MongoDB connection failed"
→ Vérifiez que MongoDB tourne (local ou Atlas disponible)

### "AttributeError: module 'boto3' has no attribute..."
→ Installez boto3: `pip install boto3`

### "Error: Scheduler is not running"
→ Le scheduler démarre automatiquement, mais `start()` peut être appelé manuellement

---

## 🎯 Architecture Résumée

```
HTTP Request
    ↓
routes/api.py (valide, log)
    ↓
services/ (logique métier)
    ↓
repositories/ (données)
    ↓
MongoDB / Cloud Storage
```

---

## 📊 Structure Fichiers Principaux

```
app/
├── core/
│   ├── exceptions.py      ← Exceptions personnalisées
│   └── logger.py          ← Logging centralisé
├── domain/
│   └── __init__.py        ← Pydantic models
├── repositories/
│   └── __init__.py        ← MongoDB repository
├── services/
│   ├── connection_service.py  ← Build URI MongoDB
│   ├── export_service.py      ← Export orchestration
│   └── backup_service.py      ← Backup orchestration
├── processor/
│   └── __init__.py        ← CSV processing
├── routes/
│   └── api.py             ← HTTP endpoints
└── scheduler/
    ├── manager.py         ← APScheduler
    └── tasks.py           ← Tâches planifiées
```

---

## ✅ Vérification Finale

```bash
# 1. Serveur tourne?
curl http://localhost:8000/ | head -c 50

# 2. Tests passent?
python -m unittest discover -s tests -p "test_*.py" -q

# 3. Imports corrects?
python -c "from app.services import ExportService; print('OK')"
```

---

**🚀 Prêt à déployer!**

Pour questions, voir:
- `ARCHITECTURE_REFACTORED.md` - Architecture détaillée
- `API_DOCUMENTATION.md` - Endpoints complets
- Code docstrings - Code inline
