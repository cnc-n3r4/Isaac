"""
Share Command - Standardized Implementation

Generate shareable links for uploaded images.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.images import CloudImageStorage


class ShareCommand(BaseCommand):
    """Generate shareable links for cloud images"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute share command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with share operation results
        """
        try:
            parser = FlagParser(args)

            # Initialize cloud storage
            storage = CloudImageStorage()

            # Determine action
            if parser.has_flag("create"):
                checksum = parser.get_flag("create")
                expires_days = int(parser.get_flag("expires", default="7"))

                # Verify image exists
                image = storage.get_image(checksum)
                if not image:
                    return CommandResponse(
                        success=False,
                        error=f"Image with checksum {checksum} not found",
                        metadata={"error_code": "IMAGE_NOT_FOUND"}
                    )

                # Generate shareable link
                share_url = storage.generate_shareable_link(checksum, expires_days)

                if share_url:
                    result = f"✅ Shareable link created for {image.filename}\n"
                    result += f"   URL: {share_url}\n"
                    result += f"   Expires: {expires_days} days"
                    return CommandResponse(
                        success=True,
                        data=result,
                        metadata={"checksum": checksum, "url": share_url}
                    )
                else:
                    return CommandResponse(
                        success=False,
                        error="Failed to create shareable link",
                        metadata={"error_code": "SHARE_CREATION_FAILED"}
                    )

            elif parser.has_flag("list"):
                shares = storage.list_shared_links()

                if not shares:
                    return CommandResponse(
                        success=True,
                        data="No active shareable links",
                        metadata={"count": 0}
                    )

                output = []
                output.append(f"📋 Active Shareable Links ({len(shares)}):")
                output.append("-" * 80)

                for share in shares:
                    output.append(f"📎 {share['filename']}")
                    output.append(f"   URL: {share['share_url']}")
                    output.append(f"   Expires: {share['expires_at']}")
                    output.append(f"   Token: {share['token']}")
                    output.append("")

                return CommandResponse(
                    success=True,
                    data="\n".join(output),
                    metadata={"count": len(shares)}
                )

            elif parser.has_flag("revoke"):
                token = parser.get_flag("revoke")

                success = storage.revoke_share_link(token)

                if success:
                    return CommandResponse(
                        success=True,
                        data=f"✅ Shareable link revoked: {token}",
                        metadata={"token": token}
                    )
                else:
                    return CommandResponse(
                        success=False,
                        error=f"Failed to revoke shareable link: {token}",
                        metadata={"error_code": "REVOKE_FAILED"}
                    )

            else:
                return CommandResponse(
                    success=False,
                    error="Usage: /share --create <checksum> | /share --list | /share --revoke <token>",
                    metadata={"error_code": "INVALID_ACTION"}
                )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "SHARE_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="share",
            description="Generate shareable links for uploaded cloud images",
            usage="/share [--create <checksum> [--expires <days>]|--list|--revoke <token>]",
            examples=[
                "/share --create abc123 --expires 7    # Create link expiring in 7 days",
                "/share --list                         # List all active shareable links",
                "/share --revoke xyz789                # Revoke a shareable link"
            ],
            tier=2,  # Needs validation - cloud operation
            aliases=["share-link"],
            category="file"
        )
