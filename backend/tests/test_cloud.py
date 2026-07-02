"""Tests for cloud uploaders"""

import unittest
import sys
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
        
        # Test upload
        success = uploader.upload_file(b"test data", "test.csv")
        self.assertTrue(success)
    
    def test_factory_unknown_provider(self):
        """Test factory raises error for unknown provider"""
        with self.assertRaises(ValueError):
            get_uploader("unknown_provider")
    
    def test_factory_case_insensitive(self):
        """Test factory is case insensitive"""
        uploader1 = get_uploader("mock")
        uploader2 = get_uploader("MOCK")
        uploader3 = get_uploader("MoMo")
        
        self.assertEqual(uploader1.__class__.__name__, "MockUploader")
        self.assertEqual(uploader2.__class__.__name__, "MockUploader")
        self.assertEqual(uploader3.__class__.__name__, "MockUploader")
    
    def test_factory_gdrive_aliases(self):
        """Test Google Drive aliases"""
        # Should accept gdrive, google, google_drive
        for provider in ["gdrive", "google", "google_drive"]:
            uploader = get_uploader(provider, {
                "credentials_file": "dummy.json",
                "folder_id": "dummy_id"
            })
            self.assertEqual(uploader.__class__.__name__, "GoogleDriveUploader")


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
    
    @patch('app.cloud.s3.boto3', side_effect=ImportError)
    def test_s3_boto3_not_installed(self, mock_boto3):
        """Test S3 when boto3 not installed"""
        uploader = S3Uploader(bucket_name="mybucket")
        
        with self.assertRaises(ImportError):
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
    
    @patch('app.cloud.dropbox.dropbox.Dropbox')
    def test_dropbox_path_normalization(self, mock_dropbox_class):
        """Test Dropbox path normalization"""
        mock_dbx = MagicMock()
        mock_dropbox_class.return_value = mock_dbx
        
        uploader = DropboxUploader(access_token="test_token")
        uploader.upload_file(b"test data", "path/file.csv")
        
        # Path should be normalized with leading slash
        call_args = mock_dbx.files_upload.call_args
        self.assertTrue(call_args[0][1].startswith("/"))


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
    
    @patch('app.cloud.gdrive.service_account')
    @patch('app.cloud.gdrive.build')
    @patch('builtins.open', new_callable=mock_open, read_data='{"type": "service_account"}')
    def test_gdrive_upload_success(self, mock_file, mock_build, mock_service_account):
        """Test successful Google Drive upload"""
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        uploader = GoogleDriveUploader(
            credentials_file="test_creds.json",
            folder_id="folder123"
        )
        
        result = uploader.upload_file(b"test data", "file.csv")
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
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

    def test_dropbox_uploader(self):
        mock_dropbox = MagicMock()
        mock_client = MagicMock()
        mock_dropbox.Dropbox.return_value = mock_client
        
        with patch.dict(sys.modules, {"dropbox": mock_dropbox}):
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

    @patch("app.cloud.gdrive.os.path.exists")
    def test_gdrive_uploader(self, mock_exists):
        # Simuler l'existence du fichier credentials.json
        mock_exists.return_value = True
        
        mock_service_account = MagicMock()
        mock_credentials = MagicMock()
        mock_service_account.Credentials.from_service_account_file.return_value = mock_credentials
        
        mock_discovery = MagicMock()
        mock_client = MagicMock()
        mock_discovery.build.return_value = mock_client
        
        mock_http = MagicMock()
        
        # Nous devons mocker le package google et googleapiclient
        mock_google_oauth = MagicMock()
        mock_google_oauth.service_account = mock_service_account
        
        mock_googleapiclient_discovery = MagicMock()
        mock_googleapiclient_discovery.build = mock_discovery.build
        
        mock_googleapiclient_http = MagicMock()
        mock_googleapiclient_http.MediaIoBaseUpload = mock_http.MediaIoBaseUpload
        
        modules_patch = {
            "google.oauth2": mock_google_oauth,
            "google.oauth2.service_account": mock_service_account,
            "googleapiclient": MagicMock(),
            "googleapiclient.discovery": mock_googleapiclient_discovery,
            "googleapiclient.http": mock_googleapiclient_http
        }
        
        with patch.dict(sys.modules, modules_patch):
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
            mock_discovery.build.assert_called_once_with('drive', 'v3', credentials=mock_credentials)
            mock_client.files().create.assert_called_once()

if __name__ == "__main__":
    unittest.main()
