"""Tests for cloud uploaders"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from app.cloud.factory import get_uploader
from app.cloud.s3 import S3Uploader
from app.cloud.dropbox import DropboxUploader
from app.cloud.gdrive import GoogleDriveUploader


class TestCloudFactory(unittest.TestCase):
    """Test cloud uploader factory"""
    
    def test_factory_mock_uploader(self):
        """Test factory returns mock uploader"""
        uploader = get_uploader("mock")
        self.assertEqual(uploader.__class__.__name__, "MockUploader")
        success = uploader.upload_file(b"test data", "test.csv")
        self.assertTrue(success)
    
    def test_factory_unknown_provider(self):
        """Test factory raises error for unknown provider"""
        with self.assertRaises(ValueError):
            get_uploader("unknown_provider")


class TestS3Uploader(unittest.TestCase):
    """Test S3 uploader"""
    
    @patch('app.cloud.s3.boto3')
    def test_s3_upload_success(self, mock_boto3):
        """Test successful S3 upload"""
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client
        
        uploader = S3Uploader(
            aws_access_key_id="key",
            aws_secret_access_key="secret",
            region_name="us-east-1",
            bucket_name="mybucket"
        )
        
        result = uploader.upload_file(b"test data", "path/file.csv")
        self.assertTrue(result)
        mock_client.upload_fileobj.assert_called_once()
    
    def test_s3_no_bucket_configured(self):
        """Test S3 without bucket configuration"""
        uploader = S3Uploader()
        with self.assertRaises(ValueError):
            uploader.upload_file(b"test data", "file.csv")


class TestDropboxUploader(unittest.TestCase):
    """Test Dropbox uploader"""
    
    @patch('app.cloud.dropbox.dropbox')
    def test_dropbox_upload_success(self, mock_dropbox_module):
        """Test successful Dropbox upload"""
        mock_dbx = MagicMock()
        mock_dropbox_module.Dropbox.return_value = mock_dbx
        
        uploader = DropboxUploader(access_token="test_token")
        result = uploader.upload_file(b"test data", "path/file.csv")
        
        self.assertTrue(result)
        mock_dbx.files_upload.assert_called_once()
    
    def test_dropbox_no_token_configured(self):
        """Test Dropbox without token"""
        uploader = DropboxUploader()
        with self.assertRaises(ValueError):
            uploader.upload_file(b"test data", "file.csv")


class TestGoogleDriveUploader(unittest.TestCase):
    """Test Google Drive uploader"""
    
    def test_gdrive_no_credentials(self):
        """Test Google Drive without credentials file"""
        uploader = GoogleDriveUploader(credentials_file=None)
        with self.assertRaises(ValueError):
            uploader.upload_file(b"test data", "file.csv")
    
    def test_gdrive_credentials_not_found(self):
        """Test Google Drive with missing credentials file"""
        uploader = GoogleDriveUploader(credentials_file="/nonexistent/path.json")
        with self.assertRaises(FileNotFoundError):
            uploader.upload_file(b"test data", "file.csv")


if __name__ == "__main__":
    unittest.main()
