"""Tests for cloud uploaders"""

import sys
from unittest.mock import MagicMock

# Mock optional cloud SDK packages to allow tests to run without them installed
mock_boto3 = MagicMock()
mock_dropbox = MagicMock()
mock_google = MagicMock()
mock_google_oauth = MagicMock()
mock_googleapi = MagicMock()

sys.modules['boto3'] = mock_boto3
sys.modules['dropbox'] = mock_dropbox
sys.modules['google'] = mock_google
sys.modules['google.oauth2'] = mock_google_oauth
sys.modules['google.oauth2.service_account'] = mock_google_oauth
sys.modules['googleapiclient'] = mock_googleapi
sys.modules['googleapiclient.discovery'] = mock_googleapi
sys.modules['googleapiclient.http'] = mock_googleapi

import unittest
from unittest.mock import patch, mock_open
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
    
    def test_s3_no_bucket_configured(self):
        """Test S3 without bucket configuration"""
        uploader = S3Uploader()
        
        # Should raise ValueError for missing bucket
        with self.assertRaises(ValueError):
            uploader.upload_file(b"test data", "file.csv")


class TestDropboxUploader(unittest.TestCase):
    """Test Dropbox uploader"""
    
    def test_dropbox_upload_success(self):
        """Test successful Dropbox upload"""
        mock_dbx = MagicMock()
        mock_dropbox.Dropbox.return_value = mock_dbx
        
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
