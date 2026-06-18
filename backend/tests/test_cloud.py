import unittest
from unittest.mock import patch, MagicMock
from app.cloud.factory import get_uploader
from app.cloud.base import CloudUploader
from app.cloud.s3 import S3Uploader
from app.cloud.dropbox import DropboxUploader
from app.cloud.gdrive import GoogleDriveUploader

class TestCloudUploader(unittest.TestCase):
    def test_factory_returns_correct_uploader(self):
        # Test mock provider
        uploader = get_uploader("mock")
        self.assertEqual(uploader.__class__.__name__, "MockUploader")
        
        # Test mock write
        success = uploader.upload_file(b"test", "test.csv")
        self.assertTrue(success)

        # Test factory error for unknown provider
        with self.assertRaises(ValueError):
            get_uploader("unknown_provider")

    @patch("app.cloud.s3.boto3")
    def test_s3_uploader(self, mock_boto3):
        # Configuration du mock boto3 client
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        uploader = get_uploader("s3", {
            "aws_access_key_id": "test_key",
            "aws_secret_access_key": "test_secret",
            "region_name": "us-east-1",
            "bucket_name": "test_bucket"
        })
        
        self.assertIsInstance(uploader, S3Uploader)
        success = uploader.upload_file(b"test_content", "dest.csv")
        self.assertTrue(success)
        
        mock_boto3.client.assert_called_once_with(
            "s3",
            aws_access_key_id="test_key",
            aws_secret_access_key="test_secret",
            region_name="us-east-1"
        )
        mock_client.upload_fileobj.assert_called_once()

    @patch("app.cloud.dropbox.dropbox")
    def test_dropbox_uploader(self, mock_dropbox):
        mock_client = MagicMock()
        mock_dropbox.Dropbox.return_value = mock_client
        
        uploader = get_uploader("dropbox", {
            "access_token": "test_token"
        })
        
        self.assertIsInstance(uploader, DropboxUploader)
        success = uploader.upload_file(b"test_content", "dest.csv")
        self.assertTrue(success)
        
        mock_dropbox.Dropbox.assert_called_once_with("test_token")
        mock_client.files_upload.assert_called_once_with(
            b"test_content",
            "/dest.csv",
            mode=mock_dropbox.files.WriteMode.overwrite
        )

    @patch("app.cloud.gdrive.build")
    @patch("app.cloud.gdrive.service_account")
    @patch("app.cloud.gdrive.os.path.exists")
    def test_gdrive_uploader(self, mock_exists, mock_service_account, mock_build):
        # Simuler l'existence du fichier credentials.json
        mock_exists.return_value = True
        
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        mock_client = MagicMock()
        mock_build.return_value = mock_client
        
        uploader = get_uploader("gdrive", {
            "credentials_file": "credentials.json",
            "folder_id": "folder123"
        })
        
        self.assertIsInstance(uploader, GoogleDriveUploader)
        success = uploader.upload_file(b"test_content", "dest.csv")
        self.assertTrue(success)
        
        mock_service_account.Credentials.from_service_account_file.assert_called_once_with(
            "credentials.json",
            scopes=['https://www.googleapis.com/auth/drive']
        )
        mock_build.assert_called_once_with('drive', 'v3', credentials=mock_credentials)
        mock_client.files().create.assert_called_once()

if __name__ == "__main__":
    unittest.main()
