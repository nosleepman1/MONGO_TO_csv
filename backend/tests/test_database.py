import unittest
from app.models import ExportRequest
from app.database import build_mongo_uri

class TestDatabase(unittest.TestCase):
    def test_build_mongo_uri_direct(self):
        req = ExportRequest(uri="mongodb://localhost:27017/", db="test", collection="coll")
        self.assertEqual(build_mongo_uri(req), "mongodb://localhost:27017/")

    def test_build_mongo_uri_atlas_no_dot(self):
        req = ExportRequest(
            cluster="cluster0",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        self.assertEqual(build_mongo_uri(req), "mongodb+srv://user:pass@cluster0.mongodb.net/")

    def test_build_mongo_uri_atlas_with_one_dot(self):
        req = ExportRequest(
            cluster="cluster0.vvtqpfm",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        self.assertEqual(build_mongo_uri(req), "mongodb+srv://user:pass@cluster0.vvtqpfm.mongodb.net/")

    def test_build_mongo_uri_atlas_already_complete(self):
        req = ExportRequest(
            cluster="cluster0.vvtqpfm.mongodb.net",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        self.assertEqual(build_mongo_uri(req), "mongodb+srv://user:pass@cluster0.vvtqpfm.mongodb.net/")

    def test_build_mongo_uri_custom_domain(self):
        req = ExportRequest(
            cluster="mongo.mycompany.com",
            username="user",
            password="pass",
            db="test",
            collection="coll"
        )
        # 3 parts (2 dots): should not append .mongodb.net
        self.assertEqual(build_mongo_uri(req), "mongodb+srv://user:pass@mongo.mycompany.com/")

    def test_build_mongo_uri_url_encoding(self):
        req = ExportRequest(
            cluster="cluster0",
            username="user@name",
            password="pwd/with:special",
            db="test",
            collection="coll"
        )
        expected = "mongodb+srv://user%40name:pwd%2Fwith%3Aspecial@cluster0.mongodb.net/"
        self.assertEqual(build_mongo_uri(req), expected)

if __name__ == "__main__":
    unittest.main()
