"""
Tests for Phase 1: Cloud Image Storage - Image Upload Service
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from isaac.images.cloud_storage import CloudImageStorage, ImageMetadata


class TestCloudImageStorage:
    """Test the cloud image storage service"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.storage = CloudImageStorage(config_path=str(self.temp_dir))

    def teardown_method(self):
        """Cleanup test environment"""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_image(self, filename="test.jpg", content=b"fake image data"):
        """Create a test image file"""
        image_path = self.temp_dir / filename
        with open(image_path, 'wb') as f:
            f.write(content)
        return image_path

    def test_is_supported_image(self):
        """Test image format detection"""
        # Create test files
        jpg_path = self.create_test_image("test.jpg")
        txt_path = self.create_test_image("test.txt", b"text content")

        assert self.storage.is_supported_image(jpg_path) == True
        assert self.storage.is_supported_image(txt_path) == False
        assert self.storage.is_supported_image(Path("nonexistent.jpg")) == False

    @patch('isaac.images.cloud_storage.CloudImageStorage._upload_to_cloud')
    def test_upload_image_success(self, mock_upload):
        """Test successful image upload"""
        mock_upload.return_value = "https://cloud.example.com/images/test.jpg"

        image_path = self.create_test_image("test.jpg", b"fake jpeg data")
        result = self.storage.upload_image(image_path)

        assert result is not None
        assert result.filename == "test.jpg"
        assert result.cloud_url == "https://cloud.example.com/images/test.jpg"
        assert result.file_size == len(b"fake jpeg data")
        assert result.mime_type == "image/jpeg"

        # Verify metadata was saved
        checksum = result.checksum
        saved = self.storage.get_image(checksum)
        assert saved is not None
        assert saved.filename == result.filename

    @patch('isaac.images.cloud_storage.CloudImageStorage._upload_to_cloud')
    def test_upload_image_duplicate(self, mock_upload):
        """Test uploading the same image twice"""
        mock_upload.return_value = "https://cloud.example.com/images/test.jpg"

        image_path = self.create_test_image("test.jpg", b"duplicate data")

        # Upload first time
        result1 = self.storage.upload_image(image_path)
        assert result1 is not None

        # Upload second time - should return existing metadata
        result2 = self.storage.upload_image(image_path)
        assert result2 is not None
        assert result1.checksum == result2.checksum

        # Should only call upload once
        assert mock_upload.call_count == 1

    def test_upload_image_unsupported_format(self):
        """Test uploading unsupported file format"""
        txt_path = self.create_test_image("test.txt", b"text file")
        result = self.storage.upload_image(txt_path)

        assert result is None

    @patch('isaac.images.cloud_storage.CloudImageStorage._upload_to_cloud')
    def test_upload_image_cloud_failure(self, mock_upload):
        """Test handling of cloud upload failure"""
        mock_upload.return_value = None

        image_path = self.create_test_image("test.jpg")
        result = self.storage.upload_image(image_path)

        assert result is None

    def test_list_images_empty(self):
        """Test listing images when none uploaded"""
        images = self.storage.list_images()
        assert images == []

    @patch('isaac.images.cloud_storage.CloudImageStorage._upload_to_cloud')
    def test_list_images(self, mock_upload):
        """Test listing uploaded images"""
        mock_upload.return_value = "https://cloud.example.com/images/test.jpg"

        # Upload multiple images
        image1 = self.create_test_image("test1.jpg", b"fake jpeg data 1")
        image2 = self.create_test_image("test2.jpg", b"fake jpeg data 2")

        result1 = self.storage.upload_image(image1)
        result2 = self.storage.upload_image(image2)

        images = self.storage.list_images()

        assert len(images) == 2
        # Should be sorted by upload time, most recent first
        assert images[0].filename in ["test1.jpg", "test2.jpg"]
        assert images[1].filename in ["test1.jpg", "test2.jpg"]

    def test_search_images(self):
        """Test searching images by filename"""
        # This would need actual uploaded images to test properly
        # For now, just test empty search
        results = self.storage.search_images("test")
        assert results == []

    @patch('isaac.images.cloud_storage.CloudImageStorage._upload_to_cloud')
    def test_delete_image(self, mock_upload):
        """Test deleting an uploaded image"""
        mock_upload.return_value = "https://cloud.example.com/images/test.jpg"

        image_path = self.create_test_image("test.jpg")
        result = self.storage.upload_image(image_path)

        assert result is not None
        checksum = result.checksum

        # Verify it exists
        assert self.storage.get_image(checksum) is not None

        # Delete it
        success = self.storage.delete_image(checksum)
        assert success == True

        # Verify it's gone
        assert self.storage.get_image(checksum) is None

    def test_delete_nonexistent_image(self):
        """Test deleting a non-existent image"""
        success = self.storage.delete_image("nonexistent")
        assert success == False


class TestImageMetadata:
    """Test the ImageMetadata dataclass"""

    def test_metadata_creation(self):
        """Test creating ImageMetadata"""
        from datetime import datetime

        metadata = ImageMetadata(
            filename="test.jpg",
            original_path="/path/to/test.jpg",
            cloud_url="https://cloud.example.com/test.jpg",
            checksum="abc123"
        )

        assert metadata.filename == "test.jpg"
        assert metadata.original_path == "/path/to/test.jpg"
        assert metadata.cloud_url == "https://cloud.example.com/test.jpg"
        assert metadata.checksum == "abc123"
        assert metadata.uploaded_at is not None
        assert isinstance(metadata.uploaded_at, datetime)

    def test_metadata_defaults(self):
        """Test ImageMetadata default values"""
        metadata = ImageMetadata(
            filename="test.jpg",
            original_path="/path/to/test.jpg",
            cloud_url="https://cloud.example.com/test.jpg",
            checksum="abc123"
        )

        assert metadata.file_size == 0
        assert metadata.mime_type == ""
        assert metadata.width is None
        assert metadata.height is None
        assert metadata.thumbnail_url is None