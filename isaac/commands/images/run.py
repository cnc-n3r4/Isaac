#!/usr/bin/env python3
"""
Images command for Isaac - Phase 1 Cloud Image Storage
Browse uploaded images with history and thumbnails.
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.images import CloudImageStorage


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def format_datetime(dt: Optional[datetime]) -> str:
    """Format datetime for display"""
    if dt is None:
        return "Unknown"
    return dt.strftime("%Y-%m-%d %H:%M")


def main():
    """Main entry point for images command"""
    # Parse arguments (simple positional parsing for now)
    action = "history"
    query = None
    checksum = None
    limit = 10

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--action" and i + 1 < len(args):
            action = args[i + 1]
            i += 2
        elif args[i] == "--query" and i + 1 < len(args):
            query = args[i + 1]
            i += 2
        elif args[i] == "--checksum" and i + 1 < len(args):
            checksum = args[i + 1]
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        else:
            i += 1

    # Initialize cloud storage
    storage = CloudImageStorage()

    if action == "history":
        show_history(storage, limit)
    elif action == "search":
        if not query:
            print("Error: --query required for search action")
            return 1
        show_search_results(storage, query, limit)
    elif action == "ocrsearch":
        if not query:
            print("Error: --query required for ocrsearch action")
            return 1
        show_ocr_search_results(storage, query, limit)
    elif action == "info":
        if not checksum:
            print("Error: --checksum required for info action")
            return 1
        show_image_info(storage, checksum)
    else:
        print(f"Error: Unknown action '{action}'")
        print("Valid actions: history, search, ocrsearch, info")
        return 1

    return 0


def show_history(storage: CloudImageStorage, limit: int):
    """Show image upload history"""
    images = storage.list_images(limit)

    if not images:
        print("📭 No images uploaded yet")
        print("   Use /upload to upload your first images!")
        return

    print(f"🖼️  Recent Images ({len(images)})")
    print("=" * 80)

    for i, img in enumerate(images, 1):
        print(f"{i:2d}. 📎 {img.filename}")
        print(f"    📏 Size: {format_file_size(img.file_size)}")
        if img.width and img.height:
            print(f"    📐 Dimensions: {img.width}x{img.height}")
        print(f"    🕒 Uploaded: {format_datetime(img.uploaded_at)}")
        print(f"    🔗 URL: {img.cloud_url}")
        if img.thumbnail_url:
            print(f"    🖼️  Thumbnail: {img.thumbnail_url}")
        print(f"    🔑 Checksum: {img.checksum[:16]}...")
        print()


def show_search_results(storage: CloudImageStorage, query: str, limit: int):
    """Show search results"""
    results = storage.search_images(query)

    if not results:
        print(f"🔍 No images found matching '{query}'")
        return

    # Limit results
    results = results[:limit]

    print(f"🔍 Search Results for '{query}' ({len(results)} matches)")
    print("=" * 80)

    for i, img in enumerate(results, 1):
        print(f"{i:2d}. 📎 {img.filename}")
        print(f"    📏 Size: {format_file_size(img.file_size)}")
        if img.width and img.height:
            print(f"    📐 Dimensions: {img.width}x{img.height}")
        print(f"    🕒 Uploaded: {format_datetime(img.uploaded_at or datetime.now())}")
        print(f"    🔗 URL: {img.cloud_url}")
        if img.thumbnail_url:
            print(f"    🖼️  Thumbnail: {img.thumbnail_url}")
        print()


def show_ocr_search_results(storage: CloudImageStorage, query: str, limit: int):
    """Show OCR text search results"""
    results = storage.search_images_by_text(query)

    if not results:
        print(f"🔍 No images found with OCR text containing '{query}'")
        print("Note: OCR requires pytesseract and Tesseract OCR to be installed")
        return

    # Limit results
    results = results[:limit]

    print(f"🔍 OCR Search Results for '{query}' ({len(results)} matches)")
    print("=" * 80)

    for i, img in enumerate(results, 1):
        print(f"{i:2d}. 📎 {img.filename}")
        print(f"    📏 Size: {format_file_size(img.file_size)}")
        if img.width and img.height:
            print(f"    📐 Dimensions: {img.width}x{img.height}")
        print(f"    🕒 Uploaded: {format_datetime(img.uploaded_at or datetime.now())}")
        print(f"    🔗 URL: {img.cloud_url}")
        if img.thumbnail_url:
            print(f"    🖼️  Thumbnail: {img.thumbnail_url}")
        if img.ocr_confidence:
            print(f"    📝 OCR Confidence: {img.ocr_confidence:.1f}%")
        if img.ocr_text:
            # Show first 100 characters of OCR text
            ocr_preview = img.ocr_text[:100] + "..." if len(img.ocr_text) > 100 else img.ocr_text
            print(f"    📄 OCR Text: {ocr_preview}")
        print()


def show_image_info(storage: CloudImageStorage, checksum: str):
    """Show detailed information for a specific image"""
    img = storage.get_image(checksum)

    if not img:
        print(f"❌ Image with checksum {checksum} not found")
        return

    print(f"📎 Image Details")
    print("=" * 80)
    print(f"Filename: {img.filename}")
    print(f"Original Path: {img.original_path}")
    print(f"File Size: {format_file_size(img.file_size)}")
    print(f"MIME Type: {img.mime_type}")
    if img.width and img.height:
        print(f"Dimensions: {img.width}x{img.height}")
    print(f"Uploaded: {format_datetime(img.uploaded_at)}")
    print(f"Cloud URL: {img.cloud_url}")
    if img.thumbnail_url:
        print(f"Thumbnail URL: {img.thumbnail_url}")
    print(f"Checksum: {img.checksum}")

    # Check if this image has shareable links
    shares = storage.list_shared_links()
    active_shares = [s for s in shares if s['filename'] == img.filename]

    if active_shares:
        print(f"\n🔗 Shareable Links ({len(active_shares)}):")
        for share in active_shares:
            print(f"  • {share['share_url']} (expires: {share['expires_at']})")


if __name__ == "__main__":
    sys.exit(main())