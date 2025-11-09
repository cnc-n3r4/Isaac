#!/usr/bin/env python3
"""
Share command for Isaac - Phase 1 Cloud Image Storage
Generate shareable links for uploaded images.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.images import CloudImageStorage


def main():
    """Main entry point for share command"""
    if len(sys.argv) < 2:
        print("Usage: python run.py <action> [options]")
        print("Actions: create, list, revoke")
        print("Examples:")
        print("  python run.py create <checksum> [expires_days]")
        print("  python run.py list")
        print("  python run.py revoke <token>")
        return 1

    action = sys.argv[1].lower()

    # Initialize cloud storage
    storage = CloudImageStorage()

    if action == "create":
        if len(sys.argv) < 3:
            print("Error: Checksum required for create action")
            return 1

        checksum = sys.argv[2]
        expires_days = int(sys.argv[3]) if len(sys.argv) > 3 else 7

        # Verify image exists
        image = storage.get_image(checksum)
        if not image:
            print(f"Error: Image with checksum {checksum} not found")
            return 1

        # Generate shareable link
        share_url = storage.generate_shareable_link(checksum, expires_days)

        if share_url:
            print(f"✅ Shareable link created for {image.filename}")
            print(f"   URL: {share_url}")
            print(f"   Expires: {expires_days} days")
        else:
            print("❌ Failed to create shareable link")
            return 1

    elif action == "list":
        shares = storage.list_shared_links()

        if not shares:
            print("No active shareable links")
            return 0

        print(f"📋 Active Shareable Links ({len(shares)}):")
        print("-" * 80)

        for share in shares:
            print(f"📎 {share['filename']}")
            print(f"   URL: {share['share_url']}")
            print(f"   Expires: {share['expires_at']}")
            print(f"   Token: {share['token']}")
            print()

    elif action == "revoke":
        if len(sys.argv) < 3:
            print("Error: Token required for revoke action")
            return 1

        token = sys.argv[2]

        success = storage.revoke_share_link(token)

        if success:
            print(f"✅ Shareable link revoked: {token}")
        else:
            print(f"❌ Failed to revoke shareable link: {token}")
            return 1

    else:
        print(f"Error: Unknown action '{action}'")
        print("Valid actions: create, list, revoke")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())