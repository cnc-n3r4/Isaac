"""
Togrok Handler - x.ai Collection Management for Isaac
Provides /togrok commands for managing knowledge collections
"""

import os
import glob
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from xai_sdk import Client
    HAS_XAI_SDK = True
except ImportError:
    HAS_XAI_SDK = False


class TogrokHandler:
    """Handles /togrok commands for x.ai collection management."""

    def __init__(self, session_manager):
        """Initialize the Togrok handler."""
        self.session_manager = session_manager
        self.active_collection_id = None
        self.active_collection_name = None
        self.client = None

        # Initialize x.ai client if available
        if HAS_XAI_SDK:
            try:
                # Use the same API key as the main AI client (xai_api_key from config)
                api_key = self.session_manager.config.get('xai_api_key')
                if api_key:
                    # Set the environment variable for xai-sdk
                    import os
                    os.environ['XAI_API_KEY'] = api_key
                    self.client = Client()  # Now uses the configured API key
                else:
                    print("Warning: No API key configured for x.ai collections")
                    self.client = None
            except Exception as e:
                print(f"Warning: Could not initialize x.ai client: {e}")
                self.client = None
        else:
            print("Warning: xai_sdk not available. Install with: pip install xai-sdk")

    def handle_command(self, args: List[str]) -> str:
        """Main command dispatcher for /togrok commands."""
        if not args:
            return self._show_help()

        subcommand = args[0].lower()

        # Check if x.ai client is available
        if not self.client and subcommand not in ['help', 'status']:
            return "x.ai client not available. Check that xai_api_key is configured in your Isaac config and xai_sdk is installed."

        # Route to appropriate handler
        handlers = {
            'help': self._show_help,
            'status': self._show_status,
            'list': self._handle_list,
            'use': self._handle_use,
            'create': self._handle_create,
            'upload': self._handle_upload,
            'query': self._handle_query,
            'delete': self._handle_delete,
            'info': self._handle_info,
            'grokbug': self._handle_grokbug,
            'grokrefactor': self._handle_grokrefactor,
        }

        handler = handlers.get(subcommand)
        if handler:
            return handler(args[1:])
        else:
            return f"Unknown subcommand: {subcommand}. Use /togrok help for available commands."

    def _show_help(self, args=None) -> str:
        """Show help for /togrok commands."""
        return """
Isaac x.ai Collection Manager (/togrok)

CORE COMMANDS:
  /togrok list                    List all collections
  /togrok use <name>              Switch active collection
  /togrok create <name>           Create new collection
  /togrok upload <file>           Upload file to active collection
  /togrok query <question>        Query active collection
  /togrok delete <name>           Delete collection
  /togrok info                    Show active collection details

SMART PROJECT COMMANDS:
  /togrok grokbug <project>       Create debugging collection for project
  /togrok grokrefactor <project>  Create refactoring collection for project

UTILITY:
  /togrok help                    Show this help
  /togrok status                  Show system status

EXAMPLES:
  /togrok create myproject
  /togrok upload ~/docs/api.pdf
  /togrok grokbug ~/code/myapp
  /togrok query "How does authentication work?"
"""

    def _show_status(self, args=None) -> str:
        """Show system status."""
        status = []
        status.append(f"x.ai SDK: {'Available' if HAS_XAI_SDK else 'Not installed'}")
        status.append(f"Client: {'Connected' if self.client else 'Disconnected'}")
        status.append(f"Active Collection: {self.active_collection_name or 'None'}")
        return "\n".join(status)

    def _handle_list(self, args=None) -> str:
        """List all available collections."""
        try:
            collections = self.client.collections.list()
            if not collections:
                return "No collections found. Create one with /togrok create <name>"

            result = "Available Collections:\n"
            for coll in collections:
                try:
                    doc_count = len(self.client.collections.list_documents(coll.id))
                except:
                    doc_count = "?"

                active_marker = " ← active" if coll.id == self.active_collection_id else ""
                created_date = coll.created_at.strftime("%Y-%m-%d") if hasattr(coll, 'created_at') and coll.created_at else "?"
                result += f"• {coll.name} ({doc_count} docs, created: {created_date}){active_marker}\n"

            return result.strip()
        except Exception as e:
            return f"Error listing collections: {e}"

    def _handle_use(self, args: List[str]) -> str:
        """Switch active collection."""
        if not args:
            return "Usage: /togrok use <collection_name>"

        collection_name = args[0]

        try:
            collections = self.client.collections.list()
            target_coll = next((c for c in collections if c.name == collection_name), None)

            if target_coll:
                self.active_collection_id = target_coll.id
                self.active_collection_name = target_coll.name
                return f"Switched to collection: {target_coll.name}"
            else:
                return f"Collection not found: {collection_name}"
        except Exception as e:
            return f"Error switching collection: {e}"

    def _handle_create(self, args: List[str]) -> str:
        """Create new collection."""
        if not args:
            return "Usage: /togrok create <collection_name>"

        collection_name = args[0]

        try:
            # Check if collection already exists
            collections = self.client.collections.list()
            if any(c.name == collection_name for c in collections):
                return f"Collection '{collection_name}' already exists"

            # Create new collection
            collection = self.client.collections.create(name=collection_name)
            return f"Created collection: {collection.name} (ID: {collection.id})"
        except Exception as e:
            return f"Error creating collection: {e}"

    def _handle_upload(self, args: List[str]) -> str:
        """Upload file to active collection."""
        if not args:
            return "Usage: /togrok upload <file_path>"

        if not self.active_collection_id:
            return "No active collection. Use /togrok use <name> first."

        file_path = args[0]

        try:
            # Expand user path and check if file exists
            expanded_path = Path(file_path).expanduser()
            if not expanded_path.exists():
                return f"File not found: {file_path}"

            if not expanded_path.is_file():
                return f"Not a file: {file_path}"

            # Upload file
            with open(expanded_path, 'rb') as f:
                file_content = f.read()

            # Create document in collection
            doc = self.client.collections.upload_document(
                collection_id=self.active_collection_id,
                name=expanded_path.name,
                content=file_content,
                content_type=self._guess_content_type(expanded_path)
            )

            return f"Uploaded: {expanded_path.name} to {self.active_collection_name}"
        except Exception as e:
            return f"Error uploading file: {e}"

    def _handle_query(self, args: List[str]) -> str:
        """Query active collection."""
        if not args:
            return "Usage: /togrok query <question>"

        if not self.active_collection_id:
            return "No active collection. Use /togrok use <name> first."

        question = " ".join(args)

        try:
            # Query the collection
            response = self.client.collections.query(
                collection_id=self.active_collection_id,
                query=question
            )

            if hasattr(response, 'answer') and response.answer:
                return f"Answer: {response.answer}"
            else:
                return "No answer found in collection"
        except Exception as e:
            return f"Error querying collection: {e}"

    def _handle_delete(self, args: List[str]) -> str:
        """Delete collection."""
        if not args:
            return "Usage: /togrok delete <collection_name>"

        collection_name = args[0]

        try:
            collections = self.client.collections.list()
            target_coll = next((c for c in collections if c.name == collection_name), None)

            if not target_coll:
                return f"Collection not found: {collection_name}"

            # Confirm deletion (in a real implementation, you'd want user confirmation)
            self.client.collections.delete(target_coll.id)

            # Clear active collection if it was deleted
            if self.active_collection_id == target_coll.id:
                self.active_collection_id = None
                self.active_collection_name = None

            return f"Deleted collection: {collection_name}"
        except Exception as e:
            return f"Error deleting collection: {e}"

    def _handle_info(self, args=None) -> str:
        """Show active collection details."""
        if not self.active_collection_id:
            return "No active collection. Use /togrok use <name> first."

        try:
            # Get collection details
            collection = self.client.collections.get(self.active_collection_id)

            # Get document count
            documents = self.client.collections.list_documents(self.active_collection_id)
            doc_count = len(documents)

            result = f"Active Collection: {self.active_collection_name}\n"
            result += f"ID: {self.active_collection_id}\n"
            result += f"Documents: {doc_count}\n"

            if hasattr(collection, 'created_at') and collection.created_at:
                result += f"Created: {collection.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

            if doc_count > 0:
                result += "\nDocuments:\n"
                for doc in documents[:10]:  # Show first 10
                    result += f"• {doc.name}\n"
                if doc_count > 10:
                    result += f"... and {doc_count - 10} more"

            return result
        except Exception as e:
            return f"Error getting collection info: {e}"

    def _handle_grokbug(self, args: List[str]) -> str:
        """Smart debugging collection creation."""
        if not args:
            return "Usage: /togrok grokbug <project_path>"

        project_path = args[0]

        try:
            # Extract project name
            project_name = self._extract_project_name(project_path)
            collection_name = f"debug-{project_name}"

            # Create collection if it doesn't exist
            collection = self._ensure_collection(collection_name)

            # Select and upload relevant files for debugging
            files = self._select_relevant_files(project_path, "debug")
            if not files:
                return f"No relevant files found in {project_path}"

            # Upload files
            uploaded_count = self._upload_files_batch(collection.id, files)

            # Set as active collection
            self.active_collection_id = collection.id
            self.active_collection_name = collection.name

            return f"Debug collection ready: {collection.name}\nUploaded {uploaded_count} files for debugging"

        except Exception as e:
            return f"Error creating debug collection: {e}"

    def _handle_grokrefactor(self, args: List[str]) -> str:
        """Smart refactoring collection creation."""
        if not args:
            return "Usage: /togrok grokrefactor <project_path>"

        project_path = args[0]

        try:
            # Extract project name
            project_name = self._extract_project_name(project_path)
            collection_name = f"refactor-{project_name}"

            # Create collection if it doesn't exist
            collection = self._ensure_collection(collection_name)

            # Select and upload relevant files for refactoring
            files = self._select_relevant_files(project_path, "refactor")
            if not files:
                return f"No relevant files found in {project_path}"

            # Upload files
            uploaded_count = self._upload_files_batch(collection.id, files)

            # Set as active collection
            self.active_collection_id = collection.id
            self.active_collection_name = collection.name

            return f"Refactor collection ready: {collection.name}\nUploaded {uploaded_count} files for refactoring analysis"

        except Exception as e:
            return f"Error creating refactor collection: {e}"

    def _ensure_collection(self, name: str):
        """Ensure collection exists, create if needed."""
        collections = self.client.collections.list()
        existing = next((c for c in collections if c.name == name), None)

        if existing:
            return existing
        else:
            return self.client.collections.create(name=name)

    def _select_relevant_files(self, project_path: str, purpose: str) -> List[Path]:
        """Smart file selection based on project type and purpose."""
        project_path = Path(project_path).expanduser().resolve()

        if not project_path.exists():
            return []

        files = []

        # Common patterns for different purposes
        if purpose == "debug":
            # Include source code, tests, configs, error logs
            patterns = [
                "**/*.py", "**/*.js", "**/*.java", "**/*.cpp", "**/*.c", "**/*.cs",
                "**/test_*.py", "**/*test*.py", "**/*test*.js",
                "**/config*", "**/*.yml", "**/*.yaml", "**/*.json", "**/*.toml",
                "**/*.log", "**/error.log", "**/debug.log",
                "**/requirements.txt", "**/package.json", "**/Cargo.toml"
            ]
        elif purpose == "refactor":
            # Focus on source code and documentation
            patterns = [
                "**/*.py", "**/*.js", "**/*.java", "**/*.cpp", "**/*.c", "**/*.cs",
                "**/README*", "**/docs/**", "**/*.md",
                "**/architecture.*", "**/design.*"
            ]
        else:
            # Default to source files
            patterns = ["**/*.py", "**/*.js", "**/*.java", "**/*.cpp", "**/*.c"]

        for pattern in patterns:
            try:
                matches = list(project_path.glob(pattern))
                files.extend(matches)
            except:
                continue

        # Remove duplicates and limit to reasonable number
        unique_files = list(set(files))
        # Prioritize smaller files and limit total
        unique_files.sort(key=lambda f: f.stat().st_size)
        return unique_files[:50]  # Limit to 50 files to prevent overload

    def _upload_files_batch(self, collection_id: str, files: List[Path]) -> int:
        """Upload multiple files to a collection."""
        uploaded = 0
        for file_path in files:
            try:
                with open(file_path, 'rb') as f:
                    content = f.read()

                # Skip empty files
                if not content:
                    continue

                self.client.collections.upload_document(
                    collection_id=collection_id,
                    name=file_path.name,
                    content=content,
                    content_type=self._guess_content_type(file_path)
                )
                uploaded += 1
            except Exception as e:
                # Continue with other files if one fails
                continue

        return uploaded

    def _extract_project_name(self, project_path: str) -> str:
        """Extract project name from path."""
        path = Path(project_path).expanduser().resolve()
        return path.name or "unknown"

    def _guess_content_type(self, file_path: Path) -> str:
        """Guess content type based on file extension."""
        ext = file_path.suffix.lower()
        content_types = {
            '.txt': 'text/plain',
            '.md': 'text/markdown',
            '.py': 'text/x-python',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.yml': 'application/x-yaml',
            '.yaml': 'application/x-yaml',
            '.xml': 'application/xml',
            '.html': 'text/html',
            '.css': 'text/css',
            '.pdf': 'application/pdf',
        }
        return content_types.get(ext, 'text/plain')