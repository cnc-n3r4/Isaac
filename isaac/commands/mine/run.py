"""
Mine Handler - Personal file history and collection search for Isaac
Provides /mine commands for searching personal collections using xAI
"""

import os
import glob
import json
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    from xai_sdk import Client
    HAS_XAI_SDK = True
except ImportError:
    HAS_XAI_SDK = False


class MineHandler:
    """Handles /mine commands for personal collection search."""

    def __init__(self, session_manager):
        """Initialize the Mine handler."""
        self.session_manager = session_manager
        self.active_collection_id = None
        self.active_collection_name = None
        self.client = None

        # Load active collection from config
        config = self.session_manager.get_config()
        self.active_collection_id = config.get('active_collection_id')
        self.active_collection_name = config.get('active_collection_name')

        # Initialize x.ai client if available
        if HAS_XAI_SDK:
            try:
                # Get API keys from config - use nested structure
                xai_config = self.session_manager.config.get('xai', {})
                collections_config = xai_config.get('collections', {})
                
                api_key = collections_config.get('api_key')
                management_api_key = collections_config.get('management_api_key')
                
                # Fallback to old flat structure for backward compatibility
                if not api_key:
                    api_key = self.session_manager.config.get('xai_api_key')
                if not management_api_key:
                    management_api_key = self.session_manager.config.get('xai_management_api_key')
                
                if api_key:
                    # Initialize client with both API keys (management key is optional)
                    # Use configurable hosts if specified, otherwise use defaults
                    api_host = self.session_manager.config.get('xai_api_host', 'api.x.ai')
                    management_api_host = self.session_manager.config.get('xai_management_api_host', 'management-api.x.ai')
                    
                    self.client = Client(
                        api_key=api_key,
                        management_api_key=management_api_key,
                        api_host=api_host,
                        management_api_host=management_api_host,
                        timeout=3600  # Extended timeout for reasoning models
                    )
                else:
                    print("Warning: No API key configured for x.ai collections")
                    self.client = None
            except Exception as e:
                print(f"Warning: Could not initialize x.ai client: {e}")
                self.client = None

    def _save_active_collection(self):
        """Save the active collection to config."""
        config = self.session_manager.get_config()
        config['active_collection_id'] = self.active_collection_id
        config['active_collection_name'] = self.active_collection_name
        
        # Update session manager's config too
        self.session_manager.config.update(config)
        
        # Save to disk
        try:
            import json
            from pathlib import Path
            config_file = Path.home() / '.isaac' / 'config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass  # Silently fail
        else:
            print("Warning: xai_sdk not available. Install with: pip install xai-sdk")

    def handle_command(self, args: List[str]) -> str:
        """Main command dispatcher for /mine commands."""
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
            return f"Unknown subcommand: {subcommand}. Use /mine help for available commands."

    def _show_help(self, args=None) -> str:
        """Show help for /mine commands."""
        return """
Isaac x.ai Collection Manager (/mine)

CORE COMMANDS:
  /mine list                    List all collections
  /mine use <name>              Switch active collection
  /mine use <name> query <text> Switch collection and query in one command
  /mine create <name>           Create new collection
  /mine upload <file>           Upload file to active collection
  /mine query <question>        Query active collection
  /mine delete <name>           Delete collection
  /mine info                    Show active collection details

SMART PROJECT COMMANDS:
  /mine grokbug <project>       Create debugging collection for project
  /mine grokrefactor <project>  Create refactoring collection for project

UTILITY:
  /mine help                    Show this help
  /mine status                  Show system status

EXAMPLES:
  /mine create myproject
  /mine upload ~/docs/api.pdf
  /mine grokbug ~/code/myapp
  /mine query "How does authentication work?"
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
            # First try to list collections via API (requires management key)
            collections_response = self.client.collections.list()
            collections = collections_response.collections
            
            if not collections:
                return "No collections found. Create one with /mine create <name>"

            result = "Available Collections (API):\n"
            for coll in collections:
                try:
                    # Get document count
                    docs_response = self.client.collections.list_documents(coll.collection_id)
                    doc_count = len(docs_response.documents)
                except:
                    doc_count = "?"

                active_marker = " ← active" if coll.collection_id == self.active_collection_id else ""
                # Handle protobuf Timestamp
                created_date = "?"
                if hasattr(coll, 'created_at') and coll.created_at:
                    # Convert protobuf Timestamp to datetime
                    import datetime
                    timestamp_seconds = coll.created_at.seconds
                    created_date = datetime.datetime.fromtimestamp(timestamp_seconds).strftime("%Y-%m-%d")
                result += f"• {coll.collection_name} ({doc_count} docs, created: {created_date}){active_marker}\n"
            
            return result
            
        except Exception as e:
            error_msg = str(e).lower()
            if "management" in error_msg and "key" in error_msg:
                # Fallback: show configured collections from config
                config = self.session_manager.config
                configured_collections = []
                
                tc_collection_id = config.get('tc_log_collection_id')
                if tc_collection_id:
                    configured_collections.append(("tc_logs", tc_collection_id))
                
                cpf_collection_id = config.get('cpf_log_collection_id') 
                if cpf_collection_id:
                    configured_collections.append(("cpf_logs", cpf_collection_id))
                
                if configured_collections:
                    result = "Configured Collections (limited access - management API key required for full listing):\n"
                    for name, coll_id in configured_collections:
                        active_marker = " ← active" if coll_id == self.active_collection_id else ""
                        result += f"• {name} (ID: {coll_id}){active_marker}\n"
                    result += "\nTo get full collection management, obtain a management API key from x.ai"
                    return result
                else:
                    return ("Error listing collections: Please provide a management API key.\n"
                           "Get one from https://console.x.ai and set 'xai_management_api_key' in ~/.isaac/config.json")
            else:
                return f"Error listing collections: {e}"

            return result.strip()
        except Exception as e:
            return f"Error listing collections: {e}"

    def _handle_use(self, args: List[str]) -> str:
        """Switch active collection."""
        if not args:
            return "Usage: /mine use <collection_name> [query <query_text>]"

        collection_name = args[0]

        try:
            # Try to get collections from API first
            collections_response = self.client.collections.list()
            collections = collections_response.collections

            target_coll = next((c for c in collections if c.collection_name == collection_name), None)

            if target_coll:
                self.active_collection_id = target_coll.collection_id
                self.active_collection_name = target_coll.collection_name
                self._save_active_collection()
                result = f"Switched to collection: {target_coll.collection_name}"
            else:
                return f"Collection not found: {collection_name}"
        except Exception as e:
            # Fallback: use configured collections from config
            if "management" in str(e).lower() or "api key" in str(e).lower():
                config = self.session_manager.get_config()
                configured_collections = {
                    'tc_logs': config.get('tc_log_collection_id'),
                    'cpf_logs': config.get('cpf_log_collection_id')
                }

                if collection_name in configured_collections:
                    collection_id = configured_collections[collection_name]
                    if collection_id:
                        self.active_collection_id = collection_id
                        self.active_collection_name = collection_name
                        self._save_active_collection()
                        result = f"Switched to configured collection: {collection_name}"
                    else:
                        return f"Collection '{collection_name}' not configured in ~/.isaac/config.json"
                else:
                    available = [name for name, id_val in configured_collections.items() if id_val]
                    if available:
                        return f"Collection '{collection_name}' not found. Available configured collections: {', '.join(available)}"
                    else:
                        return "No collections configured. Set tc_log_collection_id or cpf_log_collection_id in ~/.isaac/config.json"
            else:
                return f"Error switching collection: {e}"

        # Check if there's a follow-up command
        if len(args) > 1 and args[1].lower() == 'query':
            query_args = args[2:]
            if query_args:
                query_result = self._handle_query(query_args)
                return f"{result}\n{query_result}"
            else:
                return f"{result}\nUsage: /mine use <collection_name> query <query_text>"

        return result

    def _handle_create(self, args: List[str]) -> str:
        """Create new collection."""
        if not args:
            return "Usage: /mine create <collection_name>"

        collection_name = args[0]

        try:
            # Check if collection already exists
            collections_response = self.client.collections.list()
            collections = collections_response.collections
            if any(c.collection_name == collection_name for c in collections):
                return f"Collection '{collection_name}' already exists"

            # Create new collection
            collection = self.client.collections.create(name=collection_name)
            return f"Created collection: {collection.collection_name} (ID: {collection.collection_id})"
        except Exception as e:
            return f"Error creating collection: {e}"

    def _handle_upload(self, args: List[str]) -> str:
        """Upload file to active collection."""
        if not args:
            return "Usage: /mine upload <file_path>"

        if not self.active_collection_id:
            return "No active collection. Use /mine use <name> first."

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
                data=file_content,
                content_type=self._guess_content_type(expanded_path)
            )

            return f"Uploaded: {expanded_path.name} to {self.active_collection_name}"
        except Exception as e:
            return f"Error uploading file: {e}"

    def _handle_query(self, args: List[str]) -> str:
        """Query active collection."""
        if not args:
            return "Usage: /mine query <question>"

        if not self.active_collection_id:
            return "No active collection. Use /mine use <name> first."

        question = " ".join(args)

        try:
            # Search the collection
            response = self.client.collections.search(
                query=question,
                collection_ids=[self.active_collection_id]
            )

            if hasattr(response, 'matches') and response.matches:
                # Return the first match
                match = response.matches[0]
                if hasattr(match, 'chunk_content'):
                    return f"Answer: {match.chunk_content}"
                else:
                    return f"Found match: {match}"
            else:
                return "No answer found in collection"
        except Exception as e:
            return f"Error querying collection: {e}"

    def _handle_delete(self, args: List[str]) -> str:
        """Delete collection."""
        if not args:
            return "Usage: /mine delete <collection_name>"

        collection_name = args[0]

        try:
            collections_response = self.client.collections.list()
            collections = collections_response.collections
            target_coll = next((c for c in collections if c.collection_name == collection_name), None)

            if not target_coll:
                return f"Collection not found: {collection_name}"

            # Confirm deletion (in a real implementation, you'd want user confirmation)
            self.client.collections.delete(target_coll.collection_id)

            # Clear active collection if it was deleted
            if self.active_collection_id == target_coll.collection_id:
                self.active_collection_id = None
                self.active_collection_name = None

            return f"Deleted collection: {collection_name}"
        except Exception as e:
            return f"Error deleting collection: {e}"

    def _handle_info(self, args=None) -> str:
        """Show active collection details."""
        if not self.active_collection_id:
            return "No active collection. Use /mine use <name> first."

        try:
            # Get collection details
            collection = self.client.collections.get(self.active_collection_id)

            # Get document count
            documents_response = self.client.collections.list_documents(self.active_collection_id)
            documents = documents_response.documents
            doc_count = len(documents)

            result = f"Active Collection: {self.active_collection_name}\n"
            result += f"ID: {self.active_collection_id}\n"
            result += f"Documents: {doc_count}\n"

            if hasattr(collection, 'created_at') and collection.created_at:
                # Handle protobuf Timestamp
                import datetime
                timestamp_seconds = collection.created_at.seconds
                created_date = datetime.datetime.fromtimestamp(timestamp_seconds).strftime('%Y-%m-%d %H:%M:%S')
                result += f"Created: {created_date}\n"

            if doc_count > 0:
                result += "\nDocuments:\n"
                for doc in documents[:10]:  # Show first 10
                    doc_name = doc.file_metadata.name if hasattr(doc, 'file_metadata') and doc.file_metadata else "Unknown"
                    result += f"• {doc_name}\n"
                if doc_count > 10:
                    result += f"... and {doc_count - 10} more"

            return result
        except Exception as e:
            return f"Error getting collection info: {e}"

    def _handle_grokbug(self, args: List[str]) -> str:
        """Smart debugging collection creation."""
        if not args:
            return "Usage: /mine grokbug <project_path>"

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
            uploaded_count = self._upload_files_batch(collection.collection_id, files)

            # Set as active collection
            self.active_collection_id = collection.collection_id
            self.active_collection_name = collection.collection_name

            return f"Debug collection ready: {collection.collection_name}\nUploaded {uploaded_count} files for debugging"

        except Exception as e:
            return f"Error creating debug collection: {e}"

    def _handle_grokrefactor(self, args: List[str]) -> str:
        """Smart refactoring collection creation."""
        if not args:
            return "Usage: /mine grokrefactor <project_path>"

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
            uploaded_count = self._upload_files_batch(collection.collection_id, files)

            # Set as active collection
            self.active_collection_id = collection.collection_id
            self.active_collection_name = collection.collection_name

            return f"Refactor collection ready: {collection.collection_name}\nUploaded {uploaded_count} files for refactoring analysis"

        except Exception as e:
            return f"Error creating refactor collection: {e}"

    def _ensure_collection(self, name: str):
        """Ensure collection exists, create if needed."""
        collections_response = self.client.collections.list()
        collections = collections_response.collections
        existing = next((c for c in collections if c.collection_name == name), None)

        if existing:
            return existing
        else:
            return self.client.collections.create(name=name)

    def _select_relevant_files(self, project_path: str, purpose: str) -> List[Path]:
        """Smart file selection based on project type and purpose."""
        project_dir = Path(project_path).expanduser().resolve()

        if not project_dir.exists():
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
                matches = list(project_dir.glob(pattern))
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
                    data=content,
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


def main():
    """Main entry point for mine command"""
    try:
        # Check if we're being called through dispatcher (stdin has JSON) or standalone
        if not sys.stdin.isatty():
            # Called through dispatcher - read JSON payload from stdin
            payload = json.loads(sys.stdin.read())
            command = payload.get('command', '')
            
            # Strip the trigger to get args
            args = []
            if command.startswith('/mine '):
                args = command[6:].strip().split()
            elif command == '/mine':
                args = []
        else:
            # Standalone execution - get args from command line
            args = sys.argv[1:] if len(sys.argv) > 1 else []
        
        # Get session manager
        from isaac.core.session_manager import SessionManager
        session = SessionManager()
        
        # Create handler and execute
        handler = MineHandler(session)
        result = handler.handle_command(args)
        
        # Return response
        if not sys.stdin.isatty():
            # Dispatcher mode - return JSON
            print(json.dumps({
                "ok": True,
                "kind": "text",
                "stdout": result,
                "meta": {}
            }))
        else:
            # Standalone mode - print result directly
            print(result)
    
    except Exception as e:
        if not sys.stdin.isatty():
            # Dispatcher mode - return JSON error
            print(json.dumps({
                "ok": False,
                "kind": "text",
                "stdout": f"Error: {e}",
                "meta": {}
            }))
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


if __name__ == "__main__":
    main()