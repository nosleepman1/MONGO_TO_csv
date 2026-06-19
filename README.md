# MongoDB to CSV Exporter & Cloud Backup Scheduler

Une application moderne et performante pour exporter vos collections MongoDB au format CSV, les nettoyer automatiquement et programmer des sauvegardes récurrentes vers vos services Cloud préférés (Amazon S3, Google Drive, Dropbox).

Le projet est structuré avec un **backend FastAPI autonome** (Python) et est prêt à accueillir un **frontend React** (TypeScript).

---

## Fonctionnalités Clés

- **Export Direct** : Téléchargement instantané au format CSV avec nettoyage automatique (aplatissement des dictionnaires imbriqués, conversion propre des tableaux en listes séparées par des virgules, exclusion de l'identifiant MongoDB `_id`).

- **Sauvegardes Cloud** : Téléversement direct et automatisé vers **Amazon S3**, **Dropbox** et **Google Drive** (avec imports de dépendances dynamiques pour plus de légèreté).

- **Planification Persistante** : Programmation de tâches via des expressions Cron standard (APScheduler). Les tâches planifiées sont stockées dans une base de données locale **SQLite** (`jobs.sqlite`) pour survivre aux redémarrages de l'application.

- **Sécurité** : Masquage automatique des identifiants et des mots de passe sensibles lors de la consultation des tâches planifiées.

- **CLI Autonome** : Un script en ligne de commande complet (`backup_cli.py`) pour exécuter des sauvegardes directement depuis un terminal ou l'intégrer à un cron système.

- **Suite de Tests complète** : 23 tests unitaires et d'intégration validant les processeurs de données, l'API et les comportements Cloud sous forme de mocks.

---

## Structure du Projet

```
MONGO_TO_csv/
├── backend/                  # Partie Serveur et Logiques Métier (Python)
│   ├── app/
│   │   ├── cloud/            # Services de téléversement Cloud (S3, Drive, Dropbox)
│   │   ├── scheduler/        # Planification des sauvegardes de fond (APScheduler)
│   │   ├── config.py         # Gestion de la configuration (.env)
│   │   ├── database.py       # Requêtes MongoDB par lots (optimisation réseau)
│   │   ├── models.py         # Modèles de données Pydantic (validation des API)
│   │   ├── processor.py      # Nettoyage et transformation CSV (Pandas)
│   │   └── routes.py         # Endpoints FastAPI
│   │
│   ├── tests/                # Tests unitaires et d'intégration (pytest/unittest)
│   ├── backup_cli.py         # Outil en ligne de commande
│   ├── main.py               # Point d'entrée de démarrage FastAPI
│   ├── requirements.txt      # Dépendances Python
│   ├── .env.example          # Modèle de variables d'environnement
│   └── jobs.sqlite           # Base locale SQLite (créée au lancement)
│
├── frontend/                 # Partie Client (React/TypeScript)
│   └── types/                # Types TypeScript synchronisés avec l'API
│
├── index.html                # Interface HTML legacy (à remplacer par React)
└── README.md                 # Ce fichier
```

---

## Démarrage du Backend

### 1. Prérequis

Assurez-vous d'avoir Python 3.8+ d'installé.

### 2. Installation des Dépendances

Rendez-vous dans le dossier backend et installez les packages :

```bash
cd backend
pip install -r requirements.txt
```

_Note sur les dépendances Cloud :_ Par défaut, le backend est léger. Si vous utilisez l'un des fournisseurs Cloud, installez uniquement la dépendance requise :

- **AWS S3** : `pip install boto3`
- **Dropbox** : `pip install dropbox`
- **Google Drive** : `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`

### 3. Configuration de l'Environnement

Copiez le modèle de configuration et éditez-le avec vos identifiants :

```bash
cp .env.example .env
```

Remplissez-y vos identifiants MongoDB et vos clés API de stockage Cloud.

### 4. Lancement du Serveur API

Démarrez le serveur de développement FastAPI (qui écoutera sur `http://127.0.0.1:8000`) :

```bash
python main.py
```

> Accédez à la documentation interactive Swagger complète et testez les endpoints directement à l'adresse : `http://127.0.0.1:8000/docs`.

### 5. Utilisation du CLI

Vous pouvez exécuter une sauvegarde directement sans lancer le serveur web.
Exemple d'exécution locale en mode simulé (Mock) :

```bash
python backup_cli.py --db ma_base --collection mes_users --provider mock --dest test_backup.csv
```

> Le fichier généré sera sauvegardé dans le répertoire `backend/mock_uploads/`.

---

## Exécution des Tests

Lancez les tests unitaires et d'intégration automatisés pour vérifier que tout fonctionne :

```bash
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

---

## Développement du Frontend React

Un dossier `/frontend/types/` contenant les définitions TypeScript (`.ts`) a été pré-généré pour faciliter l'intégration de votre frontend :

- Importez simplement les types de requêtes et de réponses pour vos requêtes fetch/axios :

```typescript
import { ExportRequest, JobsListResponse } from "../frontend/types";
```

Pour la documentation complète des routes API et des payloads JSON, veuillez vous référer à :
**`backend/workflow_and_api.md`**
