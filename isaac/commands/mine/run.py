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
                
                # Strip whitespace from API keys (common config issue)
                if api_key:
                    api_key = api_key.strip()
                if management_api_key:
                    management_api_key = management_api_key.strip()
                
                if api_key:
                    # Initialize xAI Collections client
                    # NOTE: Collections API requires a COLLECTIONS-SPECIFIC API key, NOT the Chat API key
                    # api_key: Collections API key (gRPC) - required for search, upload, document access
                    # management_api_key: Management API key (REST) - required for list, create, delete collections
                    # Get both keys from console.x.ai - they must be Collections API keys, not Chat API keys
                    api_host = collections_config.get('api_host') or self.session_manager.config.get('xai_api_host', 'api.x.ai')
                    management_api_host = collections_config.get('management_api_host') or self.session_manager.config.get('xai_management_api_host', 'management-api.x.ai')
                    
                    # Get timeout from config, default to 3600 (1 hour)
                    timeout_seconds = collections_config.get('timeout_seconds') or self.session_manager.config.get('xai_collections_timeout_seconds', 3600)
                    
                    self.client = Client(
                        api_key=api_key,
                        management_api_key=management_api_key or api_key,  # Use same key if management key not specified
                        api_host=api_host,
                        management_api_host=management_api_host,
                        timeout=timeout_seconds  # Configurable timeout for collections operations
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

    def handle_command(self, args: List[str], command: str = '/mine') -> str:
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
            'cast': self._handle_cast,
            'upload': self._handle_cast,  # Alias for backward compatibility
            'dig': self._handle_dig,
            'query': self._handle_dig,  # Alias for backward compatibility
            'delete': self._handle_delete,
            'info': self._handle_info,
            'pan': self._handle_pan,
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
  /mine use <name> dig <text>   Switch collection and dig in one command
  /mine create <name>           Create new collection
  /mine cast <file>             Cast file into active collection
  /mine dig <question>          Dig up answers from active collection
  /mine pan <collection>        List file_ids within a collection
  /mine delete <name>           Delete collection
  /mine info                    Show active collection details

ADVANCED FEATURES:
  /config console               Configure search parameters, file filtering
  - Set specific file_ids to search within collections
  - Enable "search files only" mode for targeted queries

EXAMPLES:
  /mine dig "what is machine learning?"
  /mine use mydocs dig "find all email addresses"
  /mine pan mydocs                    # List file_ids in 'mydocs' collection
  /config console  # Configure file_ids like 'file_01852dbb-3f44-45fc-8cf8-699610d17501'
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

                active_marker = " [ACTIVE]" if coll.collection_id == self.active_collection_id else ""
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
                
                # Get collections from xai.collections config (supports any collection names)
                xai_config = config.get('xai', {})
                collections_config = xai_config.get('collections', {})
                
                # Type check: collections_config must be a dict
                if collections_config and isinstance(collections_config, dict):
                    # Filter out non-collection keys (enabled, api_key, etc.)
                    reserved_keys = {'enabled', 'api_key', 'management_api_key', 'management_api_host', 
                                   'default_collection', 'active_collection_id', 'active_collection_name'}
                    
                    for coll_name, coll_id in collections_config.items():
                        # Skip reserved config keys, only process collection mappings
                        if coll_name not in reserved_keys and coll_id and isinstance(coll_id, str):
                            configured_collections.append((coll_name, coll_id))
                
                if configured_collections:
                    result = "Configured Collections (from config):\n"
                    for name, coll_id in configured_collections:
                        active_marker = " [ACTIVE]" if coll_id == self.active_collection_id else ""
                        result += f"• {name} (ID: {coll_id[:8]}...){active_marker}\n"
                    result += "\nNote: Using config-based collections. For full API listing, add 'xai_management_api_key' to config."
                    return result
                else:
                    return ("Error: No collections configured.\n"
                           "Add collections to ~/.isaac/config.json under xai.collections:\n"
                           '  "xai": {\n'
                           '    "collections": {\n'
                           '      "tc-logs": "your-collection-uuid",\n'
                           '      "cpf-logs": "your-collection-uuid",\n'
                           '      "cnc-info": "your-collection-uuid"\n'
                           '    }\n'
                           '  }')
            else:
                return f"Error listing collections: {e}"

    def _handle_use(self, args: List[str]) -> str:
        """Switch active collection."""
        if not args:
            return "Usage: /mine use <collection_name> [dig <query_text>]"

        # Remove quotes from collection name if present
        collection_name = args[0].strip('"').strip("'")

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
                xai_config = config.get('xai', {})
                configured_collections = xai_config.get('collections', {})

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
        if len(args) > 1 and args[1].lower() in ['dig', 'query']:
            dig_args = args[2:]
            if dig_args:
                dig_result = self._handle_dig(dig_args)
                return f"{result}\n{dig_result}"
            else:
                return f"{result}\nUsage: /mine use <collection_name> dig <query_text>"

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

    def _handle_cast(self, args: List[str]) -> str:
        """Cast file into active collection (down the mine)."""
        if not args:
            return "Usage: /mine cast <file_path>"

        if not self.active_collection_id:
            return "No active collection. Use /mine use <name> first."

        file_path = args[0]

        try:
            # Remove quotes if present
            file_path = file_path.strip('"').strip("'")
            
            # Expand user path (~) and environment variables
            import os
            expanded_path = os.path.expanduser(file_path)
            expanded_path = os.path.expandvars(expanded_path)
            
            # Convert to Path and resolve relative to current working directory
            expanded_path = Path(expanded_path)
            if not expanded_path.is_absolute():
                expanded_path = Path.cwd() / expanded_path
            
            # Resolve to absolute path (handles .., ., etc.)
            expanded_path = expanded_path.resolve()
            
            if not expanded_path.exists():
                return f"File not found: {file_path} (resolved to: {expanded_path})"

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

            return f"Cast into mine: {expanded_path.name} -> {self.active_collection_name}"
        except Exception as e:
            return f"Error casting file: {e}"

    def _handle_dig(self, args: List[str]) -> str:
        """Dig up answers from active collection."""
        if not args:
            return "Usage: /mine dig <question>"

        if not self.active_collection_id:
            return "No active collection. Use /mine use <name> first."

        question = " ".join(args)

        try:
            # Load mine config for search parameters
            mine_config = self._load_mine_config()
            search_files_only = mine_config.get('search_files_only', False)
            file_ids = mine_config.get('file_ids', [])

            # Search the collection
            # Note: xAI SDK has a hardcoded 10-second gRPC timeout for search operations
            # SDK returns multiple matches by default
            search_params = {
                'query': question,
                'collection_ids': [self.active_collection_id]
            }
            
            # If searching specific files only, add file_ids filter
            if search_files_only and file_ids:
                # xAI SDK may support file filtering - add if available
                search_params['file_ids'] = file_ids
            
            response = self.client.collections.search(**search_params)

            if hasattr(response, 'matches') and response.matches:
                # Return top matches with truncated content for piping-friendly output
                # Collection chunks can be huge (user-configurable) - keep output manageable
                matches = response.matches[:3]  # Top 3 matches
                
                if len(matches) == 1:
                    # Single match - return with moderate truncation
                    match = matches[0]
                    if hasattr(match, 'chunk_content'):
                        content = match.chunk_content
                        # Truncate very large chunks (keep first 2000 chars)
                        if len(content) > 2000:
                            content = content[:2000] + "\n... [content truncated]"
                        return f"Answer: {content}"
                    else:
                        return f"Found match: {match}"
                else:
                    # Multiple matches - return summary with previews
                    result = f"Found {len(response.matches)} matches:\n\n"
                    for i, match in enumerate(matches, 1):
                        if hasattr(match, 'chunk_content'):
                            # Preview only for multiple matches (500 chars each)
                            content = match.chunk_content[:500]
                            if len(match.chunk_content) > 500:
                                content += "..."
                            
                            # Include score if available
                            score = getattr(match, 'score', None)
                            score_text = f" (score: {score:.3f})" if score is not None else ""
                            
                            result += f"Match {i}{score_text}:\n{content}\n\n"
                        else:
                            result += f"Match {i}: {match}\n\n"
                    return result.strip()
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

    def _handle_pan(self, args: List[str]) -> str:
        """Pan for file_ids within a collection (list documents with their file_ids)."""
        if not args:
            return "Usage: /mine pan <collection_name>"

        collection_name = args[0]

        try:
            # Find the collection by name
            collections_response = self.client.collections.list()
            collections = collections_response.collections
            target_coll = next((c for c in collections if c.collection_name == collection_name), None)

            if not target_coll:
                return f"Collection not found: {collection_name}"

            # Get documents in the collection
            documents_response = self.client.collections.list_documents(target_coll.collection_id)
            documents = documents_response.documents

            if not documents:
                return f"No documents found in collection '{collection_name}'"

            result = f"File IDs in collection '{collection_name}' (ID: {target_coll.collection_id}):\n\n"

            for doc in documents:
                # Try to get file_id from various possible properties
                file_id = "unknown"
                # Check common ID property names
                for id_prop in ['file_id', 'id', 'document_id', 'fileId', 'documentId']:
                    if hasattr(doc, id_prop):
                        file_id = getattr(doc, id_prop)
                        break
                
                # If still unknown, try to inspect the object
                if file_id == "unknown":
                    # Look for any property that looks like an ID
                    for attr_name in dir(doc):
                        if not attr_name.startswith('_'):
                            attr_value = getattr(doc, attr_name)
                            if isinstance(attr_value, str) and (attr_value.startswith('file_') or len(attr_value) == 36):
                                file_id = attr_value
                                break

                # Get filename
                filename = "Unknown"
                if hasattr(doc, 'file_metadata') and getattr(doc, 'file_metadata'):
                    file_metadata = getattr(doc, 'file_metadata')
                    if hasattr(file_metadata, 'name'):
                        filename = getattr(file_metadata, 'name')
                
                # Fallback: check direct properties on doc
                if filename == "Unknown":
                    for name_prop in ['name', 'filename', 'file_name']:
                        if hasattr(doc, name_prop):
                            filename = getattr(doc, name_prop)
                            break

                result += f"• {filename}: {file_id}\n"

            result += f"\nTotal: {len(documents)} files"
            return result

        except Exception as e:
            return f"Error panning collection: {e}"

    def _load_mine_config(self) -> Dict[str, Any]:
        """Load mine configuration from config file."""
        config_file = Path.home() / '.isaac' / 'mine_config.json'
        defaults = {
            'max_chunk_size': 1000,
            'match_preview_length': 200,
            'multi_match_count': 5,
            'piping_threshold': 0.7,
            'piping_max_context': 3,
            'show_scores': True,
            'file_ids': [],
            'search_files_only': False
        }
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except Exception:
                pass  # Use defaults if file corrupted
        
        return defaults

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

            # Select and cast relevant files for debugging
            files = self._select_relevant_files(project_path, "debug")
            if not files:
                return f"No relevant files found in {project_path}"

            # Cast files into collection
            cast_count = self._cast_files_batch(collection.collection_id, files)

            # Set as active collection
            self.active_collection_id = collection.collection_id
            self.active_collection_name = collection.collection_name

            return f"Debug collection ready: {collection.collection_name}\nCast {cast_count} files into mine for debugging"

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

            # Select and cast relevant files for refactoring
            files = self._select_relevant_files(project_path, "refactor")
            if not files:
                return f"No relevant files found in {project_path}"

            # Cast files into collection
            cast_count = self._cast_files_batch(collection.collection_id, files)

            # Set as active collection
            self.active_collection_id = collection.collection_id
            self.active_collection_name = collection.collection_name

            return f"Refactor collection ready: {collection.collection_name}\nCast {cast_count} files into mine for refactoring analysis"

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

    def _cast_files_batch(self, collection_id: str, files: List[Path]) -> int:
        """Cast multiple files into a collection."""
        cast = 0
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
                cast += 1
            except Exception as e:
                # Continue with other files if one fails
                continue

        return cast

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
    command = '/mine'  # Default command
    return_blob = False  # Default to envelope format
    try:
        # Check if we're being called through dispatcher (stdin has JSON) or standalone
        if not sys.stdin.isatty():
            # Called through dispatcher - read JSON payload from stdin
            stdin_data = sys.stdin.read()
            
            # Try to parse as blob format first (for piping)
            try:
                blob = json.loads(stdin_data)
                if isinstance(blob, dict) and 'kind' in blob:
                    # This is piped input in blob format
                    input_content = blob.get('content', '')
                    input_kind = blob.get('kind', 'text')
                    
                    # For mine command, piped input could be used as query content
                    # Extract command from blob meta if available
                    command = blob.get('meta', {}).get('command', '/mine')
                    
                    # Parse command to get args
                    args = []
                    if command.startswith('/mine '):
                        args = command[6:].strip().split()
                    elif command == '/mine':
                        args = []
                    
                    # If no args but we have piped content, treat content as query
                    if not args and input_content.strip():
                        args = ['dig'] + input_content.strip().split()
                        
                    # This is a pipe call - return blob format
                    return_blob = True
                elif isinstance(blob, dict) and 'manifest' in blob:
                    # This is dispatcher payload
                    payload = blob
                    command = payload.get('command', '/mine')
                    args = payload.get('args', [])
                    
                    # The dispatcher may send args as a dict or list
                    # For mine command, we need args as a list of strings
                    if isinstance(args, dict):
                        # If args is a dict, extract positional args from command string
                        if command.startswith('/mine '):
                            args = command[6:].strip().split()
                        else:
                            args = []
                    # If args is already a list, use it as-is
                    
                    # This is a dispatcher call - return envelope format
                    return_blob = False
                else:
                    # Unknown JSON format, treat as plain text input for dig command
                    args = ['dig'] + stdin_data.strip().split()
                    command = '/mine'
                    return_blob = True
            except json.JSONDecodeError:
                # Not JSON, treat as plain text input for dig command
                args = ['dig'] + stdin_data.strip().split()
                command = '/mine'
                return_blob = True
        else:
            # Standalone execution - get args from command line
            args = sys.argv[1:] if len(sys.argv) > 1 else []
            command = '/mine'
        
        # Get session manager
        from isaac.core.session_manager import SessionManager
        session = SessionManager()
        
        # Create handler and execute
        handler = MineHandler(session)
        result = handler.handle_command(args, command)
        
        # Return result in appropriate format
        if not sys.stdin.isatty():
            if return_blob:
                # Piped call - return blob
                print(json.dumps({
                    "kind": "text",
                    "content": result,
                    "meta": {"command": command}
                }))
            else:
                # Dispatcher call - return envelope
                print(json.dumps({
                    "ok": True,
                    "stdout": result
                }))
        else:
            # Standalone mode - print result directly
            print(result)
    
    except Exception as e:
        if not sys.stdin.isatty():
            # Piped/dispatcher mode - return blob error
            print(json.dumps({
                "kind": "error",
                "content": f"Error: {e}",
                "meta": {"command": command}
            }))
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


if __name__ == "__main__":
    main()