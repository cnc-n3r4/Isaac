"""
Cloud Image Storage Service for Isaac
Handles uploading, storing, and managing images in cloud storage.
"""

import hashlib
import io
import json
import mimetypes
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

try:
    import pytesseract

    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

from ..core.unified_fs import UnifiedFileSystem


@dataclass
class ImageMetadata:
    """Metadata for uploaded images"""

    filename: str
    original_path: str
    cloud_url: str
    checksum: str
    file_size: int = 0
    mime_type: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    thumbnail_url: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    ocr_text: Optional[str] = None  # Extracted text from OCR
    ocr_confidence: Optional[float] = None  # OCR confidence score

    def __post_init__(self):
        if self.uploaded_at is None:
            self.uploaded_at = datetime.now()
        elif isinstance(self.uploaded_at, str):
            # Handle string dates from JSON deserialization
            try:
                self.uploaded_at = datetime.fromisoformat(self.uploaded_at)
            except ValueError:
                self.uploaded_at = datetime.now()


class CloudImageStorage:
    """
    Cloud image storage service with auto-upload capabilities.
    Integrates with UnifiedFileSystem for local/cloud operations.
    """

    SUPPORTED_FORMATS = {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/svg+xml",
        "image/bmp",
        "image/tiff",
    }

    def __init__(self, config_path: Optional[str] = None):
        self.fs = UnifiedFileSystem()
        self.config_path = Path(config_path or "~/.isaac").expanduser()
        self.config_path.mkdir(exist_ok=True)

        # Storage quota settings (in bytes)
        self.quota_file = self.config_path / "storage_quota.json"
        self._load_quota_settings()

        # Local metadata storage
        self.metadata_file = self.config_path / "image_metadata.json"
        self._load_metadata()

    def _load_quota_settings(self) -> None:
        """Load storage quota settings"""
        if self.quota_file.exists():
            try:
                with open(self.quota_file, "r") as f:
                    quota_data = json.load(f)
                    self.storage_quota = quota_data.get(
                        "quota_bytes", 1024 * 1024 * 1024
                    )  # 1GB default
                    self.quota_warning_threshold = quota_data.get("warning_percent", 80)
            except (json.JSONDecodeError, KeyError):
                self.storage_quota = 1024 * 1024 * 1024  # 1GB default
                self.quota_warning_threshold = 80
        else:
            self.storage_quota = 1024 * 1024 * 1024  # 1GB default
            self.quota_warning_threshold = 80

    def _save_quota_settings(self) -> None:
        """Save storage quota settings"""
        quota_data = {
            "quota_bytes": self.storage_quota,
            "warning_percent": self.quota_warning_threshold,
        }
        with open(self.quota_file, "w") as f:
            json.dump(quota_data, f, indent=2)

    def _load_metadata(self) -> None:
        """Load image metadata from local storage"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    data = json.load(f)
                    self.metadata = {}
                    for k, v in data.items():
                        # Convert uploaded_at string to datetime if needed
                        if "uploaded_at" in v and isinstance(v["uploaded_at"], str):
                            try:
                                v["uploaded_at"] = datetime.fromisoformat(v["uploaded_at"])
                            except ValueError:
                                v["uploaded_at"] = datetime.now()
                        self.metadata[k] = ImageMetadata(**v)
            except (json.JSONDecodeError, KeyError):
                self.metadata = {}
        else:
            self.metadata = {}

    def _save_metadata(self) -> None:
        """Save image metadata to local storage"""
        data = {
            k: {
                "filename": v.filename,
                "original_path": v.original_path,
                "cloud_url": v.cloud_url,
                "thumbnail_url": v.thumbnail_url,
                "file_size": v.file_size,
                "mime_type": v.mime_type,
                "width": v.width,
                "height": v.height,
                "uploaded_at": (
                    v.uploaded_at.isoformat() if v.uploaded_at else datetime.now().isoformat()
                ),
                "ocr_text": v.ocr_text,
                "ocr_confidence": v.ocr_confidence,
                "checksum": v.checksum,
            }
            for k, v in self.metadata.items()
        }

        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def _get_image_info(self, file_path: Path) -> Tuple[str, int]:
        """Get MIME type and file size"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = "application/octet-stream"

        file_size = file_path.stat().st_size
        return mime_type, file_size

    def is_supported_image(self, file_path: Path) -> bool:
        """Check if file is a supported image format"""
        if not file_path.exists():
            return False

        mime_type, _ = self._get_image_info(file_path)
        return mime_type in self.SUPPORTED_FORMATS

    def upload_image(self, file_path: Path, auto_thumbnail: bool = True) -> Optional[ImageMetadata]:
        """
        Upload an image to cloud storage.

        Args:
            file_path: Path to the image file
            auto_thumbnail: Whether to generate thumbnail automatically

        Returns:
            ImageMetadata if successful, None if failed
        """
        if not self.is_supported_image(file_path):
            return None

        try:
            # Calculate checksum to avoid duplicates
            checksum = self._calculate_checksum(file_path)
            if checksum in self.metadata:
                # Image already uploaded
                return self.metadata[checksum]

            # Get image info
            mime_type, file_size = self._get_image_info(file_path)

            # Check storage quota before upload
            can_upload, quota_message = self.check_quota_before_upload(file_size)
            if not can_upload:
                return None

            if quota_message:
                print(f"⚠️  {quota_message}")

            # Generate cloud path
            filename = file_path.name
            cloud_path = f"images/{checksum[:8]}/{filename}"

            # Upload to cloud (placeholder - will use actual cloud service)
            cloud_url = self._upload_to_cloud(file_path, cloud_path)

            if not cloud_url:
                return None

            # Create metadata
            metadata = ImageMetadata(
                checksum=checksum,
                filename=filename,
                original_path=str(file_path),
                cloud_url=cloud_url,
                mime_type=mime_type,
                file_size=file_size,
                uploaded_at=datetime.now(),
                thumbnail_url=None,  # Will be generated separately
            )

            # Store metadata first
            self.metadata[checksum] = metadata

            # Generate thumbnail
            thumbnail_path = self._generate_thumbnail(file_path, checksum)
            if thumbnail_path:
                metadata.thumbnail_url = str(thumbnail_path)

            # Extract text using OCR
            ocr_text, ocr_confidence = self._extract_text_from_image(file_path)
            if ocr_text:
                metadata.ocr_text = ocr_text
                metadata.ocr_confidence = ocr_confidence

            # Save metadata after all processing
            self._save_metadata()

            return metadata

        except Exception as e:
            print(f"Error uploading image {file_path}: {e}")
            return None

    def _upload_to_cloud(self, file_path: Path, cloud_path: str) -> Optional[str]:
        """
        Upload file to cloud storage.
        This is a placeholder - will be implemented with actual cloud service.
        """
        # TODO: Implement actual cloud upload (AWS S3, Cloudinary, etc.)
        # For now, simulate successful upload
        return f"https://cloud.example.com/{cloud_path}"

    def _generate_thumbnail(
        self, file_path: Path, checksum: str, max_size: Tuple[int, int] = (200, 200)
    ) -> Optional[str]:
        """
        Generate thumbnail for image using PIL.

        Args:
            file_path: Path to the original image
            checksum: SHA256 checksum for unique identification
            max_size: Maximum thumbnail size (width, height)

        Returns:
            Cloud URL of the generated thumbnail, or None if failed
        """
        try:
            # Open image with PIL
            with Image.open(file_path) as img:
                # Store original dimensions
                self.metadata[checksum].width = img.width
                self.metadata[checksum].height = img.height

                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Create thumbnail maintaining aspect ratio
                img.thumbnail(max_size, Image.Resampling.LANCZOS)

                # Save thumbnail to memory buffer
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                buffer.seek(0)

                # Generate cloud path for thumbnail
                thumbnail_path = f"thumbnails/{checksum[:8]}.jpg"

                # Upload thumbnail to cloud (placeholder - will use actual cloud service)
                thumbnail_url = self._upload_thumbnail_to_cloud(buffer.getvalue(), thumbnail_path)

                if thumbnail_url:
                    # Update metadata
                    self.metadata[checksum].thumbnail_url = thumbnail_url
                    self._save_metadata()

                return thumbnail_url

        except Exception as e:
            print(f"Error generating thumbnail for {file_path}: {e}")
            return None

    def _upload_thumbnail_to_cloud(self, thumbnail_data: bytes, cloud_path: str) -> Optional[str]:
        """
        Upload thumbnail data to cloud storage.
        This is a placeholder - will be implemented with actual cloud service.
        """
        # TODO: Implement actual cloud upload for thumbnail
        # For now, simulate successful upload
        return f"https://cloud.example.com/{cloud_path}"

    def get_image(self, checksum: str) -> Optional[ImageMetadata]:
        """Get image metadata by checksum"""
        return self.metadata.get(checksum)

    def list_images(self, limit: int = 50) -> List[ImageMetadata]:
        """List uploaded images, most recent first"""
        images = list(self.metadata.values())
        images.sort(key=lambda x: x.uploaded_at or datetime.min, reverse=True)
        return images[:limit]

    def delete_image(self, checksum: str) -> bool:
        """Delete image from cloud and local metadata"""
        if checksum not in self.metadata:
            return False

        self.metadata[checksum]

        try:
            # TODO: Delete from cloud storage
            # self._delete_from_cloud(metadata.cloud_url)

            # Remove from local metadata
            del self.metadata[checksum]
            self._save_metadata()

            return True

        except Exception as e:
            print(f"Error deleting image {checksum}: {e}")
            return False

    def generate_shareable_link(self, checksum: str, expires_in_days: int = 7) -> Optional[str]:
        """
        Generate a shareable public link for an image.

        Args:
            checksum: Checksum of the image to share
            expires_in_days: Link expiration time in days

        Returns:
            Shareable URL or None if image not found
        """
        if checksum not in self.metadata:
            return None

        # Generate a share token (simplified - in production use proper JWT/crypto)
        import secrets

        share_token = secrets.token_urlsafe(32)

        # Calculate expiration
        expiration = datetime.now() + timedelta(days=expires_in_days)

        # Store share information
        share_info = {
            "checksum": checksum,
            "token": share_token,
            "expires_at": expiration.isoformat(),
            "created_at": datetime.now().isoformat(),
        }

        # Load existing shares
        shares_file = self.config_path / "image_shares.json"
        shares = {}
        if shares_file.exists():
            try:
                with open(shares_file, "r") as f:
                    shares = json.load(f)
            except json.JSONDecodeError:
                shares = {}

        # Add new share
        shares[share_token] = share_info

        # Save shares
        with open(shares_file, "w") as f:
            json.dump(shares, f, indent=2)

        # Generate shareable URL
        return f"https://cloud.example.com/share/{share_token}"

    def get_shared_image(self, share_token: str) -> Optional[Dict]:
        """
        Get image information from a share token.

        Args:
            share_token: The share token

        Returns:
            Dict with image info and URL, or None if invalid/expired
        """
        shares_file = self.config_path / "image_shares.json"
        if not shares_file.exists():
            return None

        try:
            with open(shares_file, "r") as f:
                shares = json.load(f)
        except json.JSONDecodeError:
            return None

        if share_token not in shares:
            return None

        share_info = shares[share_token]

        # Check expiration
        expires_at = datetime.fromisoformat(share_info["expires_at"])
        if datetime.now() > expires_at:
            # Remove expired share
            del shares[share_token]
            with open(shares_file, "w") as f:
                json.dump(shares, f, indent=2)
            return None

        # Get image metadata
        checksum = share_info["checksum"]
        if checksum not in self.metadata:
            return None

        metadata = self.metadata[checksum]

        return {
            "filename": metadata.filename,
            "url": metadata.cloud_url,
            "thumbnail_url": metadata.thumbnail_url,
            "mime_type": metadata.mime_type,
            "expires_at": share_info["expires_at"],
        }

    def list_shared_links(self) -> List[Dict]:
        """
        List all active shared links.

        Returns:
            List of share information dictionaries
        """
        shares_file = self.config_path / "image_shares.json"
        if not shares_file.exists():
            return []

        try:
            with open(shares_file, "r") as f:
                shares = json.load(f)
        except json.JSONDecodeError:
            return []

        result = []
        current_time = datetime.now()

        for token, share_info in shares.items():
            expires_at = datetime.fromisoformat(share_info["expires_at"])
            if current_time > expires_at:
                continue  # Skip expired shares

            checksum = share_info["checksum"]
            if checksum not in self.metadata:
                continue  # Skip if image no longer exists

            metadata = self.metadata[checksum]
            result.append(
                {
                    "token": token,
                    "filename": metadata.filename,
                    "share_url": f"https://cloud.example.com/share/{token}",
                    "expires_at": share_info["expires_at"],
                    "created_at": share_info["created_at"],
                }
            )

        return result

    def revoke_share_link(self, share_token: str) -> bool:
        """
        Revoke a shareable link.

        Args:
            share_token: The share token to revoke

        Returns:
            True if successfully revoked, False otherwise
        """
        shares_file = self.config_path / "image_shares.json"
        if not shares_file.exists():
            return False

        try:
            with open(shares_file, "r") as f:
                shares = json.load(f)
        except json.JSONDecodeError:
            return False

        if share_token not in shares:
            return False

        del shares[share_token]

        with open(shares_file, "w") as f:
            json.dump(shares, f, indent=2)

        return True

    def _extract_text_from_image(self, file_path: Path) -> Tuple[Optional[str], Optional[float]]:
        """
        Extract text from image using OCR.

        Args:
            file_path: Path to the image file

        Returns:
            Tuple of (extracted_text, confidence_score) or (None, None) if OCR fails
        """
        if not HAS_TESSERACT:
            return None, None

        try:
            # Open image with PIL
            with Image.open(file_path) as img:
                # Convert to RGB if necessary for better OCR results
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Extract text using pytesseract
                # Get detailed data including confidence scores
                data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

                # Extract text and calculate average confidence
                text_parts = []
                confidences = []

                for i, confidence in enumerate(data["conf"]):
                    if int(confidence) > 0:  # Only include text with some confidence
                        text = data["text"][i].strip()
                        if text:
                            text_parts.append(text)
                            confidences.append(int(confidence))

                if not text_parts:
                    return None, None

                extracted_text = " ".join(text_parts)
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0

                return extracted_text, avg_confidence

        except Exception as e:
            print(f"OCR failed for {file_path}: {e}")
            return None, None

    def search_images_by_text(
        self, query: str, min_confidence: float = 30.0
    ) -> List[ImageMetadata]:
        """
        Search images by OCR text content.

        Args:
            query: Text to search for
            min_confidence: Minimum OCR confidence score (0-100)

        Returns:
            List of images containing the query text
        """
        query_lower = query.lower()
        results = []

        for metadata in self.metadata.values():
            if (
                metadata.ocr_text
                and metadata.ocr_confidence
                and metadata.ocr_confidence >= min_confidence
            ):
                if query_lower in metadata.ocr_text.lower():
                    results.append(metadata)

        return results

    def get_images_with_text(self, min_confidence: float = 30.0) -> List[ImageMetadata]:
        """
        Get all images that have OCR text extracted.

        Args:
            min_confidence: Minimum OCR confidence score

        Returns:
            List of images with OCR text
        """
        results = []
        for metadata in self.metadata.values():
            if (
                metadata.ocr_text
                and metadata.ocr_confidence
                and metadata.ocr_confidence >= min_confidence
            ):
                results.append(metadata)

        # Sort by confidence (highest first)
        results.sort(key=lambda x: x.ocr_confidence or 0, reverse=True)
        return results

    def search_images(self, query: str) -> List[ImageMetadata]:
        """Search images by filename"""
        query_lower = query.lower()
        results = []

        for metadata in self.metadata.values():
            if query_lower in metadata.filename.lower():
                results.append(metadata)

        return results

    def get_storage_usage(self) -> Dict:
        """
        Get current storage usage statistics.

        Returns:
            Dict with usage statistics
        """
        total_size = sum(img.file_size for img in self.metadata.values())
        image_count = len(self.metadata)

        usage_percent = (total_size / self.storage_quota) * 100 if self.storage_quota > 0 else 0

        return {
            "total_bytes": total_size,
            "total_images": image_count,
            "quota_bytes": self.storage_quota,
            "usage_percent": usage_percent,
            "warning_threshold": self.quota_warning_threshold,
            "is_over_quota": total_size > self.storage_quota,
            "is_near_limit": usage_percent >= self.quota_warning_threshold,
        }

    def set_storage_quota(self, quota_bytes: int, warning_percent: int = 80) -> None:
        """
        Set storage quota and warning threshold.

        Args:
            quota_bytes: Maximum storage in bytes
            warning_percent: Warning threshold percentage (0-100)
        """
        self.storage_quota = quota_bytes
        self.quota_warning_threshold = max(0, min(100, warning_percent))
        self._save_quota_settings()

    def check_quota_before_upload(self, file_size: int) -> Tuple[bool, str]:
        """
        Check if upload would exceed quota.

        Args:
            file_size: Size of file to upload in bytes

        Returns:
            Tuple of (can_upload, message)
        """
        current_usage = self.get_storage_usage()
        projected_usage = current_usage["total_bytes"] + file_size
        projected_percent = (
            (projected_usage / self.storage_quota) * 100 if self.storage_quota > 0 else 0
        )

        if projected_usage > self.storage_quota:
            return (
                False,
                f"Upload would exceed storage quota ({projected_percent:.1f}% of {self._format_bytes(self.storage_quota)})",
            )

        if projected_percent >= self.quota_warning_threshold:
            return True, f"Warning: Upload will use {projected_percent:.1f}% of storage quota"

        return True, ""

    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes in human readable format"""
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"
