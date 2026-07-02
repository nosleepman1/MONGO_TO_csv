import unittest
import pandas as pd
from app.processor import CSVProcessor

class TestProcessor(unittest.TestCase):
    def test_clean_data_empty(self):
        df = CSVProcessor.clean_data([])
        self.assertTrue(df.empty)

    def test_clean_data_basic(self):
        docs = [
            {"_id": "12345", "name": "Alice", "age": 30},
            {"_id": "67890", "name": "Bob", "age": 25}
        ]
        df = CSVProcessor.clean_data(docs)
        # Exclude _id
        self.assertNotIn("_id", df.columns)
        self.assertIn("name", df.columns)
        self.assertIn("age", df.columns)
        self.assertEqual(df.shape[0], 2)

    def test_clean_data_nested_dict(self):
        docs = [
            {"name": "Alice", "details": {"city": "Paris", "zip": "75001"}},
            {"name": "Bob", "details": {"city": "Lyon", "zip": "69002"}}
        ]
        df = CSVProcessor.clean_data(docs)
        self.assertIn("details.city", df.columns)
        self.assertIn("details.zip", df.columns)
        self.assertEqual(df.loc[0, "details.city"], "Paris")

    def test_clean_data_lists(self):
        docs = [
            {"name": "Alice", "tags": ["admin", "user"]},
            {"name": "Bob", "tags": ["user"]}
        ]
        df = CSVProcessor.clean_data(docs)
        self.assertEqual(df.loc[0, "tags"], "admin, user")
        self.assertEqual(df.loc[1, "tags"], "user")

    def test_generate_csv_bytes_bom(self):
        df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
        csv_bytes = CSVProcessor.generate_csv_bytes(df)
        
        # Check that it starts with UTF-8 BOM
        self.assertTrue(csv_bytes.startswith(b"\xef\xbb\xbf"))
        
        # Check that it contains exactly one BOM
        self.assertFalse(csv_bytes.startswith(b"\xef\xbb\xbf\xef\xbb\xbf"))

    def test_sanitize_filename(self):
        self.assertEqual(CSVProcessor.sanitize_filename("users/admins:list?.csv"), "users_admins_list_.csv")
        self.assertEqual(CSVProcessor.sanitize_filename("valid-name_123.csv"), "valid-name_123.csv")

if __name__ == "__main__":
    unittest.main()
