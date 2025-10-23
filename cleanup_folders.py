#!/usr/bin/env python3
"""
Cleanup script to remove outdated folders
"""

import shutil
import os
import sys

def remove_outdated_folders():
    """Remove home/ and work/ folders that are no longer needed"""

    folders_to_remove = [
        "home",
        "work",
        "old proman base files"  # This was moved to reference/
    ]

    for folder in folders_to_remove:
        folder_path = os.path.join(os.getcwd(), folder)
        if os.path.exists(folder_path):
            print(f"Removing {folder_path}...")
            try:
                shutil.rmtree(folder_path)
                print(f"✓ Removed {folder}")
            except Exception as e:
                print(f"✗ Failed to remove {folder}: {e}")
        else:
            print(f"Folder {folder} not found, skipping")

    print("\nCleanup complete!")
    print("Removed outdated folders: home/, work/, old proman base files/")
    print("Legacy tools preserved in: reference/")

if __name__ == "__main__":
    print("Isaac Project Cleanup Script")
    print("============================")
    print("This will remove:")
    print("- home/ (outdated codebase copy)")
    print("- work/ (outdated codebase copy)")
    print("- old proman base files/ (moved to reference/)")
    print()

    # Safety check
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm":
        remove_outdated_folders()
    else:
        print("Run with --confirm to actually delete the folders")
        print("Example: python cleanup_folders.py --confirm")