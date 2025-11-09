#!/usr/bin/env python3
"""
Upload command for Isaac - Phase 1 Cloud Image Storage
"""

import sys
import glob
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.images import CloudImageStorage


def main():
    """Main entry point for upload command"""
    if len(sys.argv) < 2:
        print("Usage: python run.py <comma-separated-file-paths>")
        print("Example: python run.py image1.jpg,image2.png")
        return 1

    # Get file paths from command line
    paths_arg = sys.argv[1]
    path_strings = [p.strip() for p in paths_arg.split(',') if p.strip()]

    if not path_strings:
        print("Error: No file paths provided")
        return 1

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
                print(f"Warning: Path not found: {path_str}")

    if not file_paths:
        print("Error: No valid files found")
        return 1

    # Initialize cloud storage
    storage = CloudImageStorage()

    uploaded_count = 0
    failed_count = 0

    print(f"Found {len(file_paths)} files to process:")
    for path_str in file_paths:
        path = Path(path_str)
        print(f"  - {path.name}")

    print("\nUploading images...")

    for path_str in file_paths:
        path = Path(path_str)

        if not storage.is_supported_image(path):
            print(f"⚠️  Skipping unsupported format: {path.name}")
            failed_count += 1
            continue

        print(f"📤 Uploading {path.name}...")
        result = storage.upload_image(path)

        if result:
            print(f"✅ Uploaded: {result.filename}")
            print(f"   URL: {result.cloud_url}")
            if result.thumbnail_url:
                print(f"   Thumbnail: {result.thumbnail_url}")
            uploaded_count += 1
        else:
            print(f"❌ Failed to upload: {path.name}")
            failed_count += 1

    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successful: {uploaded_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📁 Total processed: {len(file_paths)}")

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())