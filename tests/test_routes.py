import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

class TestRoutes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_read_root(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("MongoToCSV", response.text)

    @patch("app.routes.fetch_mongodb_documents")
    def test_export_csv_success(self, mock_fetch):
        # Mock le retour de la base de données
        mock_fetch.return_value = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]

        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "users"
        }
        
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "text/csv; charset=utf-8")
        self.assertIn("attachment; filename=users_export.csv", response.headers["content-disposition"])
        
        # Décode en UTF-8 avec BOM pour vérifier le contenu
        content = response.content.decode("utf-8-sig")
        self.assertIn("name,age", content)
        self.assertIn("Alice,30", content)
        self.assertIn("Bob,25", content)

    @patch("app.routes.fetch_mongodb_documents")
    def test_export_csv_empty_collection(self, mock_fetch):
        mock_fetch.return_value = []

        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "empty"
        }
        
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Aucun document trouvé", response.json()["detail"])

    @patch("app.routes.fetch_mongodb_documents")
    def test_export_csv_connection_error(self, mock_fetch):
        mock_fetch.side_effect = ConnectionError("Erreur de connexion MongoDB ou authentification échouée")

        payload = {
            "uri": "mongodb://localhost:27017/",
            "db": "testdb",
            "collection": "users"
        }
        
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Erreur de connexion MongoDB ou authentification échouée")

    def test_export_csv_validation_error(self):
        # Manque le nom de base de données et de collection
        payload = {
            "uri": "mongodb://localhost:27017/"
        }
        response = self.client.post("/export-csv", json=payload)
        self.assertEqual(response.status_code, 422)
        # Doit contenir les détails d'erreurs de validation Pydantic
        self.assertIn("detail", response.json())

if __name__ == "__main__":
    unittest.main()
