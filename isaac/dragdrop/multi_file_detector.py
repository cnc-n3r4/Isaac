"""
Smart Drag-Drop System for Isaac
Handles multi-file detection, analysis, and intelligent routing.
"""

import mimetypes
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


class FileCategory(Enum):
    """Categories for file classification"""

    IMAGE = "image"
    DOCUMENT = "document"
    CODE = "code"
    ARCHIVE = "archive"
    VIDEO = "video"
    AUDIO = "audio"
    EXECUTABLE = "executable"
    CONFIG = "config"
    TEXT = "text"
    OTHER = "other"


@dataclass
class FileAnalysis:
    """Analysis result for a single file"""

    path: Path
    category: FileCategory
    mime_type: str
    size_bytes: int
    extension: str
    is_supported: bool
    metadata: Optional[Dict] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchAnalysis:
    """Analysis result for multiple files"""

    files: List[FileAnalysis]
    total_size: int
    categories: Dict[FileCategory, int]
    supported_count: int
    unsupported_count: int
    duplicates: List[Path]  # Files with same content

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def has_images(self) -> bool:
        return self.categories.get(FileCategory.IMAGE, 0) > 0

    @property
    def has_documents(self) -> bool:
        return self.categories.get(FileCategory.DOCUMENT, 0) > 0

    @property
    def has_code(self) -> bool:
        return self.categories.get(FileCategory.CODE, 0) > 0

    @property
    def is_mixed_batch(self) -> bool:
        """True if batch contains multiple different file types"""
        return len([cat for cat, count in self.categories.items() if count > 0]) > 1


class MultiFileDetector:
    """
    Detects and analyzes multiple files for intelligent drag-drop handling.
    """

    # Supported file extensions by category
    SUPPORTED_EXTENSIONS = {
        FileCategory.IMAGE: {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".tif",
            ".webp",
            ".svg",
            ".ico",
        },
        FileCategory.DOCUMENT: {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".txt",
            ".rtf",
            ".odt",
        },
        FileCategory.CODE: {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".cs",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".toml",
            ".md",
            ".rst",
            ".sh",
            ".bash",
            ".ps1",
            ".sql",
            ".r",
            ".m",
            ".swift",
            ".kt",
            ".scala",
        },
        FileCategory.ARCHIVE: {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar", ".iso"},
        FileCategory.VIDEO: {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v"},
        FileCategory.AUDIO: {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a"},
        FileCategory.EXECUTABLE: {".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".appimage"},
        FileCategory.CONFIG: {".ini", ".cfg", ".conf", ".config", ".env", ".properties"},
    }

    # MIME type prefixes for additional detection
    MIME_PREFIXES = {
        FileCategory.IMAGE: ["image/"],
        FileCategory.VIDEO: ["video/"],
        FileCategory.AUDIO: ["audio/"],
        FileCategory.DOCUMENT: [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats",
        ],
        FileCategory.ARCHIVE: ["application/zip", "application/x-tar", "application/gzip"],
    }

    def __init__(self):
        self._checksum_cache = {}  # Cache for duplicate detection

    def analyze_files(self, file_paths: List[str]) -> BatchAnalysis:
        """
        Analyze multiple files and return comprehensive batch analysis.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            BatchAnalysis with detailed file information
        """
        if not file_paths:
            return BatchAnalysis([], 0, {}, 0, 0, [])

        # Convert to Path objects and filter existing files
        paths = []
        for path_str in file_paths:
            path = Path(path_str).expanduser().resolve()
            if path.exists() and path.is_file():
                paths.append(path)
            else:
                print(f"Warning: File not found or not accessible: {path_str}")

        if not paths:
            return BatchAnalysis([], 0, {}, 0, 0, [])

        # Analyze each file
        analyses = []
        total_size = 0
        categories = {}
        supported_count = 0
        checksums_seen = set()

        for path in paths:
            analysis = self._analyze_single_file(path)
            analyses.append(analysis)

            total_size += analysis.size_bytes

            # Count categories
            categories[analysis.category] = categories.get(analysis.category, 0) + 1

            if analysis.is_supported:
                supported_count += 1

            # Check for duplicates (same checksum)
            if analysis.metadata and analysis.metadata.get("checksum"):
                checksum = analysis.metadata["checksum"]
                if checksum in checksums_seen:
                    # This is a duplicate
                    pass  # We'll collect duplicates later
                checksums_seen.add(checksum)

        # Find duplicates by checking which files have the same checksum
        duplicates = []
        checksum_to_paths = {}
        for analysis in analyses:
            if analysis.metadata and analysis.metadata.get("checksum"):
                checksum = analysis.metadata["checksum"]
                if checksum not in checksum_to_paths:
                    checksum_to_paths[checksum] = []
                checksum_to_paths[checksum].append(analysis.path)

        for paths_list in checksum_to_paths.values():
            if len(paths_list) > 1:
                duplicates.extend(paths_list[1:])  # All except the first are duplicates

        unsupported_count = len(analyses) - supported_count

        return BatchAnalysis(
            files=analyses,
            total_size=total_size,
            categories=categories,
            supported_count=supported_count,
            unsupported_count=unsupported_count,
            duplicates=duplicates,
        )

    def _analyze_single_file(self, path: Path) -> FileAnalysis:
        """
        Analyze a single file and determine its category and properties.

        Args:
            path: Path to the file to analyze

        Returns:
            FileAnalysis with file details
        """
        # Get basic file info
        try:
            stat = path.stat()
            size_bytes = stat.st_size
        except OSError:
            size_bytes = 0

        extension = path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(path))

        if not mime_type:
            mime_type = "application/octet-stream"

        # Determine category
        category = self._determine_category(extension, mime_type)

        # Check if supported (we can handle this type)
        is_supported = self._is_supported_type(category, extension, mime_type)

        # Additional metadata
        metadata = {}

        # Calculate checksum for duplicate detection (only for reasonable file sizes)
        if size_bytes > 0 and size_bytes < 100 * 1024 * 1024:  # < 100MB
            try:
                checksum = self._calculate_checksum(path)
                metadata["checksum"] = checksum
            except Exception:
                pass

        return FileAnalysis(
            path=path,
            category=category,
            mime_type=mime_type,
            size_bytes=size_bytes,
            extension=extension,
            is_supported=is_supported,
            metadata=metadata,
        )

    def _determine_category(self, extension: str, mime_type: str) -> FileCategory:
        """
        Determine the file category based on extension and MIME type.

        Args:
            extension: File extension (lowercase, with dot)
            mime_type: MIME type string

        Returns:
            FileCategory enum value
        """
        # Check by extension first
        for category, extensions in self.SUPPORTED_EXTENSIONS.items():
            if extension in extensions:
                return category

        # Check by MIME type prefix
        for category, prefixes in self.MIME_PREFIXES.items():
            for prefix in prefixes:
                if mime_type.startswith(prefix):
                    return category

        # Special cases
        if mime_type == "text/plain":
            return FileCategory.TEXT

        if mime_type.startswith("text/"):
            return FileCategory.CODE  # Treat as code if it's text-based

        # Default to OTHER
        return FileCategory.OTHER

    def _is_supported_type(self, category: FileCategory, extension: str, mime_type: str) -> bool:
        """
        Determine if Isaac can handle this file type.

        Args:
            category: File category
            extension: File extension
            mime_type: MIME type

        Returns:
            True if the file type is supported
        """
        # Images are always supported (we have image storage)
        if category == FileCategory.IMAGE:
            return True

        # Code files are supported (can be analyzed, edited, etc.)
        if category == FileCategory.CODE:
            return True

        # Documents are supported (can be analyzed, OCR'd if needed)
        if category == FileCategory.DOCUMENT:
            return True

        # Text files are supported
        if category == FileCategory.TEXT:
            return True

        # Archives might be supported for extraction
        if category == FileCategory.ARCHIVE:
            return extension in [".zip", ".tar", ".gz"]  # Common ones

        # Config files are supported
        if category == FileCategory.CONFIG:
            return True

        # Videos and audio have limited support
        if category in [FileCategory.VIDEO, FileCategory.AUDIO]:
            return False  # Not supported yet

        # Executables are not supported for security
        if category == FileCategory.EXECUTABLE:
            return False

        # Everything else is not supported
        return False

    def _calculate_checksum(self, path: Path) -> str:
        """
        Calculate SHA256 checksum of file.

        Args:
            path: Path to file

        Returns:
            Hex string of SHA256 checksum
        """
        import hashlib

        if path in self._checksum_cache:
            return self._checksum_cache[path]

        hash_sha256 = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        except Exception:
            return ""

        checksum = hash_sha256.hexdigest()
        self._checksum_cache[path] = checksum
        return checksum

    def get_recommended_action(self, analysis: BatchAnalysis) -> str:
        """
        Get recommended action based on batch analysis.

        Args:
            analysis: BatchAnalysis result

        Returns:
            String describing recommended action
        """
        if analysis.file_count == 0:
            return "No valid files found"

        if analysis.file_count == 1:
            file = analysis.files[0]
            if file.category == FileCategory.IMAGE:
                return "Upload image to cloud storage"
            elif file.category == FileCategory.CODE:
                return "Analyze code file"
            elif file.category == FileCategory.DOCUMENT:
                return "Process document"
            else:
                return f"Handle {file.category.value} file"

        # Multiple files
        if analysis.is_mixed_batch:
            return f"Process {analysis.file_count} mixed files ({', '.join(f'{count} {cat.value}' for cat, count in analysis.categories.items() if count > 0)})"

        # Same type batch
        dominant_category = max(analysis.categories.items(), key=lambda x: x[1])[0]

        if dominant_category == FileCategory.IMAGE:
            return f"Upload {analysis.categories[FileCategory.IMAGE]} images to cloud storage"
        elif dominant_category == FileCategory.CODE:
            return f"Analyze {analysis.categories[FileCategory.CODE]} code files"
        elif dominant_category == FileCategory.DOCUMENT:
            return f"Process {analysis.categories[FileCategory.DOCUMENT]} documents"
        else:
            return f"Handle {analysis.file_count} {dominant_category.value} files"
