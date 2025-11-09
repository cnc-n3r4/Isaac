"""
Upload Command - Standardized Implementation

Upload images to cloud storage with automatic processing.
"""

import glob
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.images import CloudImageStorage


class UploadCommand(BaseCommand):
    """Upload images to cloud storage"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute upload command.

        Args:
            args: Command arguments (file paths, comma-separated or as positional args)
            context: Optional execution context

        Returns:
            CommandResponse with upload results
        """
        try:
            parser = FlagParser(args)

            # Get file paths from positional arguments
            positional = parser.get_all_positional()

            if not positional:
                return CommandResponse(
                    success=False,
                    error="Usage: /upload <file1> [file2] [...]\nExample: /upload image1.jpg image2.png",
                    metadata={"error_code": "NO_FILES"}
                )

            # Parse file paths (handle comma-separated or space-separated)
            path_strings = []
            for arg in positional:
                if "," in arg:
                    # Comma-separated paths
                    path_strings.extend([p.strip() for p in arg.split(",") if p.strip()])
                else:
                    path_strings.append(arg)

            if not path_strings:
                return CommandResponse(
                    success=False,
                    error="No file paths provided",
                    metadata={"error_code": "NO_FILES"}
                )

            # Expand glob patterns and resolve paths
            file_paths = []
            for path_str in path_strings:
                # Expand glob patterns
                matches = glob.glob(path_str)
                if matches:
                    file_paths.extend(matches)
                else:
                    # Check if it's a direct file path
                    path = Path(path_str).expanduser()
                    if path.exists():
                        file_paths.append(str(path))
                    else:
                        # Keep track of not found, but continue
                        pass

            if not file_paths:
                return CommandResponse(
                    success=False,
                    error="No valid files found",
                    metadata={"error_code": "NO_VALID_FILES"}
                )

            # Initialize cloud storage
            storage = CloudImageStorage()

            uploaded_count = 0
            failed_count = 0
            results = []

            results.append(f"Found {len(file_paths)} files to process:")
            for path_str in file_paths:
                path = Path(path_str)
                results.append(f"  - {path.name}")

            results.append("\nUploading images...")

            for path_str in file_paths:
                path = Path(path_str)

                if not storage.is_supported_image(path):
                    results.append(f"⚠️  Skipping unsupported format: {path.name}")
                    failed_count += 1
                    continue

                results.append(f"📤 Uploading {path.name}...")
                result = storage.upload_image(path)

                if result:
                    results.append(f"✅ Uploaded: {result.filename}")
                    results.append(f"   URL: {result.cloud_url}")
                    if result.thumbnail_url:
                        results.append(f"   Thumbnail: {result.thumbnail_url}")
                    uploaded_count += 1
                else:
                    results.append(f"❌ Failed to upload: {path.name}")
                    failed_count += 1

            results.append(f"\n📊 Upload Summary:")
            results.append(f"   ✅ Successful: {uploaded_count}")
            results.append(f"   ❌ Failed: {failed_count}")
            results.append(f"   📁 Total processed: {len(file_paths)}")

            return CommandResponse(
                success=failed_count == 0,
                data="\n".join(results),
                metadata={
                    "uploaded": uploaded_count,
                    "failed": failed_count,
                    "total": len(file_paths)
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "UPLOAD_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="upload",
            description="Upload images to cloud storage with automatic processing",
            usage="/upload <file1> [file2] [...]",
            examples=[
                "/upload image1.jpg image2.png        # Upload multiple images",
                "/upload *.jpg                        # Upload all JPG files",
                "/upload ~/Pictures/photo.png        # Upload from home directory"
            ],
            tier=2,  # Needs validation - file upload to cloud
            aliases=["up", "img-upload"],
            category="file"
        )
