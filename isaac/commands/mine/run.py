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

    def __init__(self, session_manager_or_config):
        """Initialize the Mine handler."""
        if hasattr(session_manager_or_config, 'get_config'):
            # It's a SessionManager
            self.session_manager = session_manager_or_config
            self.config = self.session_manager.get_config()
        elif isinstance(session_manager_or_config, dict) and 'config' in session_manager_or_config:
            # It's session data from dispatcher with config
            self.session_manager = None
            self.config = session_manager_or_config['config']
        else:
            # It's a config dict (fallback)
            self.session_manager = None
            self.config = session_manager_or_config
        
        self.active_collection_id = None
        self.active_collection_name = None
        self.client = None
        self.warnings = []  # Collect warnings instead of printing them

        # Load active collection from config
        self.active_collection_id = self.config.get('active_collection_id')
        self.active_collection_name = self.config.get('active_collection_name')

        # Load mine-specific settings from config console
        self._load_mine_settings()

    def _load_mine_settings(self):
        """Load mine-specific settings from config console."""
        import json
        from pathlib import Path
        
        # Default settings (match config console defaults)
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
        
        # Load from mine_config.json if it exists
        config_file = Path.home() / '.isaac' / 'mine_config.json'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    defaults.update(loaded)
            except Exception:
                pass  # Use defaults if file corrupted
        
        # Store settings
        self.mine_settings = defaults

        # Initialize x.ai client if available
        if HAS_XAI_SDK:
            try:
                # Get API keys from config - use nested structure
                xai_config = self.config.get('xai', {})
                collections_config = xai_config.get('collections', {})
                
                api_key = collections_config.get('api_key')
                management_api_key = collections_config.get('management_api_key')
                
                # Fallback to old flat structure for backward compatibility
                if not api_key:
                    api_key = self.config.get('xai_api_key')
                if not management_api_key:
                    management_api_key = self.config.get('xai_management_api_key')
                
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
                    api_host = collections_config.get('api_host') or self.config.get('xai_api_host', 'api.x.ai')
                    management_api_host = collections_config.get('management_api_host') or self.config.get('xai_management_api_host', 'management-api.x.ai')
                    
                    # Get timeout from config, default to 3600 (1 hour)
                    timeout_seconds = collections_config.get('timeout_seconds') or self.config.get('xai_collections_timeout_seconds', 3600)
                    
                    self.client = Client(
                        api_key=api_key,
                        management_api_key=management_api_key or api_key,  # Use same key if management key not specified
                        api_host=api_host,
                        management_api_host=management_api_host,
                        timeout=timeout_seconds  # Configurable timeout for collections operations
                    )
                else:
                    self.warnings.append("Warning: No API key configured for x.ai collections")
                    self.client = None
            except Exception as e:
                print(f"Warning: Could not initialize x.ai client: {e}")
                self.client = None

    def _save_active_collection(self):
        """Save the active collection to config."""
        config = self.config.copy()
        config['active_collection_id'] = self.active_collection_id
        config['active_collection_name'] = self.active_collection_name
        
        # Update session manager's config too
        if self.session_manager:
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

    def parse_command_flags(self, args: List[str]) -> Dict[str, Any]:
        """Parse command arguments using standardized -/-- flag syntax.
        
        Supports:
        - --flag value
        - --flag=value  
        - -f value
        - -f=value
        - --flag (boolean flags)
        
        Returns dict with parsed flags and remaining positional args.
        """
        parsed = {}
        positional = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            # Check if it's a flag (starts with -)
            if arg.startswith('--'):
                # Long flag like --flag or --flag=value
                if '=' in arg:
                    flag, value = arg.split('=', 1)
                    flag = flag[2:]  # Remove --
                    parsed[flag] = value
                else:
                    flag = arg[2:]  # Remove --
                    # Check if next arg is the value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        parsed[flag] = args[i + 1]
                        i += 1  # Skip the value
                    else:
                        parsed[flag] = True  # Boolean flag
                        
            elif arg.startswith('-') and len(arg) > 1:
                # Short flag like -f or -f=value
                if '=' in arg:
                    flag, value = arg.split('=', 1)
                    flag = flag[1:]  # Remove -
                    parsed[flag] = value
                else:
                    flag = arg[1:]  # Remove -
                    # Check if next arg is the value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        parsed[flag] = args[i + 1]
                        i += 1  # Skip the value
                    else:
                        parsed[flag] = True  # Boolean flag
            else:
                # Positional argument
                positional.append(arg)
                
            i += 1
            
        return {
            'flags': parsed,
            'positional': positional
        }

    def handle_command(self, args: List[str], command: str = '/mine') -> str:
        """Main command dispatcher for /mine commands."""
        # Format warnings at the beginning
        warning_text = ""
        if self.warnings:
            warning_text = "\n".join(self.warnings) + "\n"
        
        if not args:
            return warning_text + self._show_help()

        # Parse command flags
        parsed = self.parse_command_flags(args)
        flags = parsed['flags']
        positional = parsed['positional']

        # Check if x.ai client is available
        if not self.client and not any(flag in ['help', 'status', 'list', 'deed', 'info'] for flag in flags):
            return "x.ai client not available. Check that xai_api_key is configured in your Isaac config and xai_sdk is installed."

        # COLLECTION ARRAY MANAGEMENT
        if 'drift' in flags:
            return self._handle_drift([flags['drift']] + positional)
        elif 'claim' in flags and 'to-drift' not in flags:
            # Simple collection claim (not combined with sub-group)
            return self._handle_claim([flags['claim']] + positional)

        # COLLECTION MANAGEMENT
        elif 'stake' in flags:
            return self._handle_stake([flags['stake']] + positional)
        elif 'abandon' in flags:
            return self._handle_abandon([flags['abandon']] + positional)

        # FILE ARRAY MANAGEMENT
        elif 'skip' in flags:
            return self._handle_skip([flags['skip']] + positional)

        # ORE PROCESSING (UPLOAD)
        elif 'muck' in flags:
            return self._handle_muck([flags['muck']] + positional)

        # EXPLORATION & SEARCH
        elif 'survey' in flags:
            return self._handle_survey([flags['survey']] + positional)
        elif 'dig' in flags:
            return self._handle_dig([flags['dig']] + positional)

        # FILE OPERATIONS
        elif 'haul' in flags:
            return self._handle_haul([flags['haul']] + positional)
        elif 'pan' in flags:
            return self._handle_pan([flags['pan']] + positional)
        elif 'drop' in flags:
            return self._handle_drop([flags['drop']] + positional)

        # INFORMATION & MANAGEMENT
        elif 'list' in flags or 'deed' in flags:
            if 'deed' in flags and positional and positional[0] == '--all':
                return self._handle_list()
            else:
                return self._handle_info()
        elif 'info' in flags:
            return self._handle_info()
        elif 'nuggets' in flags:
            return self._handle_nuggets(positional)
        elif 'help' in flags:
            return self._show_help()
        elif 'status' in flags:
            return self._show_status()

        # LEGACY SUPPORT (deprecated)
        elif 'use' in flags:
            self._show_deprecation_warning('use', 'claim')
            return self._handle_claim([flags['use']] + positional)
        elif 'create' in flags:
            self._show_deprecation_warning('create', 'stake')
            return self._handle_stake([flags['create']] + positional)
        elif 'cast' in flags:
            self._show_deprecation_warning('cast', 'muck')
            return self._handle_muck([flags['cast']] + positional)
        elif 'delete' in flags:
            self._show_deprecation_warning('delete', 'abandon')
            return self._handle_abandon([flags['delete']] + positional)

        else:
            return "Unknown command. Use /mine --help for available commands."

    def _show_deprecation_warning(self, old_command: str, new_command: str) -> None:
        """Show deprecation warning for old commands."""
        print(f"⚠️  Warning: --{old_command} is deprecated. Use --{new_command} instead.")

    def _handle_stake(self, args: List[str]) -> str:
        """Stake a new claim (create collection)."""
        return self._handle_create(args)  # Reuse existing create logic

    def _handle_claim(self, args: List[str]) -> str:
        """Claim/use a staked claim (switch collection)."""
        if not args:
            return "Usage: /mine --claim <collection_name> [--dig <query>]"

        collection_name = args[0]
        remaining_args = args[1:]

        # Handle combined claim and dig
        if remaining_args and remaining_args[0] == '--dig' and len(remaining_args) > 1:
            # Switch collection and dig in one command
            result = self._handle_use([collection_name])
            if "Switched to collection" in result:
                return result + "\n" + self._handle_dig(remaining_args[1:])
            else:
                return result

        # Just switch collection
        return self._handle_use([collection_name])

    def _handle_drift(self, args: List[str]) -> str:
        """Carve a drift within active claim (create sub-collection)."""
        # For now, treat as regular collection creation
        # Future: implement sub-collection hierarchy
        return self._handle_create(args)

    def _handle_muck(self, args: List[str]) -> str:
        """Muck file into active drift (upload file)."""
        return self._handle_cast(args)

    def _handle_haul(self, args: List[str]) -> str:
        """Haul file out of active drift (extract by file_id or nugget name)."""
        if not args:
            return "Usage: /mine --haul <file_id>        # Extract file content by ID\n       /mine --haul <nugget_name>    # Extract file by saved nugget name"

        target = args[0]

        # Check if it's a nugget name first
        nuggets = self.config.get('xai', {}).get('collections', {}).get('nuggets', {})

        if target in nuggets:
            # It's a nugget name - get the file_id
            nugget_data = nuggets[target]
            file_id = nugget_data['file_id']
            return self._handle_haul_extract(file_id)
        elif target.startswith('file_') or (len(target) == 36 and '-' in target):
            # Extract file by ID
            return self._handle_haul_extract(target)
        else:
            return "Usage: /mine --haul <file_id>        # Extract file content by ID\n       /mine --haul <nugget_name>    # Extract file by saved nugget name"

    def _handle_haul_extract(self, file_id: str) -> str:
        """Extract and display file content by file_id (haul out from the mine)."""
        if not self.active_collection_id:
            return "No active collection. Use /mine --claim <name> first."

        try:
            # Get all documents in the active collection
            documents_response = self.client.collections.list_documents(self.active_collection_id)
            documents = documents_response.documents

            # Find the document with matching file_id
            target_doc = None
            for doc in documents:
                # Check various possible ID fields
                doc_file_id = None
                for id_field in ['file_id', 'id', 'document_id', 'fileId', 'documentId']:
                    if hasattr(doc, id_field):
                        doc_file_id = getattr(doc, id_field)
                        break

                # Also check nested file_metadata
                if not doc_file_id and hasattr(doc, 'file_metadata') and doc.file_metadata:
                    if hasattr(doc.file_metadata, 'file_id'):
                        doc_file_id = doc.file_metadata.file_id

                if doc_file_id == file_id:
                    target_doc = doc
                    break

            if not target_doc:
                return f"File with ID '{file_id}' not found in active collection '{self.active_collection_name}'"

            # Extract file content and metadata
            filename = "Unknown"
            content = "No content available"

            # Get filename
            if hasattr(target_doc, 'file_metadata') and getattr(target_doc, 'file_metadata'):
                file_metadata = getattr(target_doc, 'file_metadata')
                if hasattr(file_metadata, 'name'):
                    filename = getattr(file_metadata, 'name')

            # Get content - try searching for the file content since direct content access may not be available
            # Use the file_id to search within this specific file
            try:
                # Note: xAI Collections API doesn't provide direct file content retrieval
                # Files are indexed for search, but full content download isn't supported
                # This is a limitation of the current xAI Collections API design
                content = "⚠️  File content retrieval not available\n\n"
                content += f"This file ({filename}) has been indexed for search in the xAI Collections API.\n"
                content += "Full file content download is not currently supported by the API.\n\n"
                content += "To search within this file, use:\n"
                content += "/mine --dig \"your question\" (searches active collection)\n\n"
                content += "File details:\n"
                content += f"• Size: {target_doc.file_metadata.size_bytes} bytes\n"
                content += f"• Type: {target_doc.file_metadata.content_type}\n"
                content += f"• Hash: {target_doc.file_metadata.hash}"
                
            except Exception as search_error:
                content = f"Unable to retrieve content: {search_error}"

            # Format output
            result = f"📄 Extracted File: {filename}\n"
            result += f"🆔 File ID: {file_id}\n"
            result += f"📚 Collection: {self.active_collection_name}\n"
            result += "=" * 50 + "\n"
            result += content

            return result

        except Exception as e:
            return f"Error extracting file: {e}"

    def _handle_nuggets(self, args: List[str]) -> str:
        """Manage saved nuggets (named file_ids for easy reference)."""
        if not args:
            # List all saved nuggets
            return self._list_nuggets()
        elif args[0] == 'save' and len(args) > 1:
            # Save piped file_ids as nuggets
            return self._save_nuggets_from_pipe(args[1:])
        elif args[0] == 'search' and len(args) > 1:
            # Search nuggets by name
            return self._search_nuggets(args[1])
        else:
            return "Usage: /mine --nuggets                    # List saved nuggets\n       /mine --nuggets save <collection>  # Save file_ids as nuggets\n       /mine --nuggets search <query>     # Search nuggets by name"

    def _list_nuggets(self) -> str:
        """List all saved nuggets."""
        nuggets = self.config.get('xai', {}).get('collections', {}).get('nuggets', {})

        if not nuggets:
            return "No nuggets saved. Use '/mine --pan <collection> | /mine --nuggets save <collection>' to save file_ids as named nuggets."

        result = "💎 Saved Nuggets (named file_ids):\n\n"
        for name, data in nuggets.items():
            file_id = data.get('file_id', 'unknown')
            collection = data.get('collection', 'unknown')
            filename = data.get('filename', 'unknown')
            result += f"• {name}: {filename} ({file_id[:20]}...)\n  Collection: {collection}\n\n"

        result += f"Total: {len(nuggets)} nuggets\n"
        result += "Use '/mine --haul <nugget_name>' to extract a nugget."
        return result

    def _save_nuggets_from_pipe(self, args: List[str]) -> str:
        """Save file_ids from piped input as named nuggets."""
        if not args:
            return "Usage: /mine --nuggets save <collection_name>"

        collection_name = args[0]

        # Read from stdin (piped input)
        import sys
        piped_data = sys.stdin.read().strip()

        if not piped_data:
            return "No piped input detected. Use: /mine --pan <collection> | /mine --nuggets save <collection>"

        # Parse file_ids from piped data
        nuggets = {}
        lines = piped_data.split('\n')

        for line in lines:
            line = line.strip()
            if line.startswith('• ') and ': ' in line:
                parts = line[2:].split(': ', 1)
                if len(parts) == 2:
                    filename, file_id = parts
                    # Create a readable nugget name from filename
                    nugget_name = self._create_nugget_name(filename, list(nuggets.keys()))
                    nuggets[nugget_name] = {
                        'file_id': file_id,
                        'filename': filename,
                        'collection': collection_name
                    }

        if not nuggets:
            return "No valid file_ids found in piped input."

        # Save nuggets to config
        if self.session_manager:
            config = self.session_manager.get_config()
        else:
            # When using config dict, we can't save - return error
            return "Cannot save nuggets when called through piping. Nuggets can only be saved in interactive mode."
        
        if 'xai' not in config:
            config['xai'] = {}
        if 'collections' not in config['xai']:
            config['xai']['collections'] = {}
        if 'nuggets' not in config['xai']['collections']:
            config['xai']['collections']['nuggets'] = {}

        config['xai']['collections']['nuggets'].update(nuggets)

        # Save to disk
        try:
            import json
            from pathlib import Path
            config_file = Path.home() / '.isaac' / 'config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            return f"Error saving nuggets: {e}"

        return f"Saved {len(nuggets)} nuggets from {collection_name}:\n" + "\n".join(f"  • {name} → {data['filename']}" for name, data in nuggets.items())

    def _search_nuggets(self, query: str) -> str:
        """Search nuggets by name."""
        nuggets = self.config.get('xai', {}).get('collections', {}).get('nuggets', {})

        matches = {}
        for name, data in nuggets.items():
            if query.lower() in name.lower() or query.lower() in data.get('filename', '').lower():
                matches[name] = data

        if not matches:
            return f"No nuggets found matching '{query}'."

        result = f"🔍 Nuggets matching '{query}':\n\n"
        for name, data in matches.items():
            file_id = data.get('file_id', 'unknown')
            filename = data.get('filename', 'unknown')
            collection = data.get('collection', 'unknown')
            result += f"• {name}: {filename}\n  ID: {file_id}\n  Collection: {collection}\n\n"

        return result

    def _create_nugget_name(self, filename: str, existing_names: List[str]) -> str:
        """Create a unique, readable nugget name from filename."""
        # Remove extension and clean up
        name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        # Replace spaces and special chars with underscores
        name = ''.join(c if c.isalnum() or c in '._-' else '_' for c in name)
        # Ensure uniqueness
        base_name = name
        counter = 1
        while name in existing_names:
            name = f"{base_name}_{counter}"
            counter += 1
        return name

    def _handle_deed(self, args: List[str]) -> str:
        """Deed the claim: show collection details."""
        if args and args[0] == '--all':
            return self._handle_list()
        else:
            return self._handle_info()

    def _handle_abandon(self, args: List[str]) -> str:
        """Abandon claim (delete collection)."""
        return self._handle_delete(args)

    def _show_help(self, args=None) -> str:
        """Show help for /mine commands."""
        return """
Isaac x.ai Collection Manager (/mine) - Mining Metaphor Edition 🏔️⛏️

COLLECTION ARRAY MANAGEMENT:
  /mine --drift <name>          # Create named array of xAI collections
  /mine --claim <array>         # Switch to collection array

COLLECTION MANAGEMENT:
  /mine --stake <name>          # Create new xAI collection
  /mine --claim <name>          # Switch to collection
  /mine --claim <name> --to-drift <subgroup>  # Switch to collection and sub-group
  /mine --abandon <collection>  # Delete collection

FILE ARRAY MANAGEMENT:
  /mine --skip <name>           # Create named array of files across collections

ORE PROCESSING (UPLOAD):
  /mine --muck <file>           # Upload file to active collection
  /mine --muck <file> --to-drift <subgroup>  # Upload to specific sub-group

EXPLORATION & SEARCH:
  /mine --survey <query>        # Search across all collections
  /mine --survey <query> --to-map <subgroup>  # Survey with sub-group focus
  /mine --dig <question>        # Search within active collection
  /mine --dig <question> --to-drift <subgroup>  # Search within sub-group
  /mine --dig -c <question>     # Search all collections
  /mine --dig -h <question>     # Search with detailed output

FILE OPERATIONS:
  /mine --haul <file>           # Attach file for analysis
  /mine --haul <file> --to-skip <array>  # Attach and associate with file array
  /mine --pan <query>           # Query attached file
  /mine --drop <file>           # Delete file from collection

INFORMATION & MANAGEMENT:
  /mine --list                  # List all collections
  /mine --info                  # Show active collection details
  /mine --nuggets               # List saved nuggets
  /mine --status                # Show system status
  /mine --help                  # Show this help

EXAMPLES:
  # Collection workflow
  /mine --stake mydocs          # Create collection
  /mine --claim mydocs          # Switch to collection
  /mine --muck document.pdf     # Upload file
  /mine --dig "find tutorials"  # Search collection

  # Cross-collection search
  /mine --survey "machine learning"  # Search all collections

  # File analysis
  /mine --pan mydocs | /mine --haul file_abc123  # Attach file
  /mine --pan "explain this code"  # Query attached file

  # Array management
  /mine --drift research        # Create collection array
  /mine --skip favorites        # Create file array
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
                except Exception:
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
                xai_config = self.config.get('xai', {})
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
            self.client.collections.upload_document(
                collection_id=self.active_collection_id,
                name=expanded_path.name,
                data=file_content,
                content_type=self._guess_content_type(expanded_path)
            )

            return f"Cast into mine: {expanded_path.name} -> {self.active_collection_name}"
        except Exception as e:
            return f"Error casting file: {e}"

    def _handle_skip(self, args: List[str]) -> str:
        """Create a named array of files across collections."""
        if not args:
            return "Usage: /mine --skip <name>    # Create named file array"

        array_name = args[0]

        # Initialize file arrays structure if it doesn't exist
        if 'xai' not in self.config:
            self.config['xai'] = {}
        if 'collections' not in self.config['xai']:
            self.config['xai']['collections'] = {}
        if 'file_arrays' not in self.config['xai']['collections']:
            self.config['xai']['collections']['file_arrays'] = {}

        file_arrays = self.config['xai']['collections']['file_arrays']

        if array_name in file_arrays:
            return f"File array '{array_name}' already exists."

        # Create empty file array
        file_arrays[array_name] = []

        # Save to disk
        self._save_active_collection()

        return f"Created file array: {array_name}"

    def _handle_survey(self, args: List[str]) -> str:
        """Survey across all collections for files and previews."""
        if not args:
            return "Usage: /mine --survey <query> [--to-map <subgroup>]"

        query = args[0]

        # TODO: Implement --to-map flag for subgroup focus
        # subgroup_focus = None
        # if len(args) > 2 and args[1] == '--to-map':
        #     subgroup_focus = args[2]

        try:
            # Get all collections
            collections_response = self.client.collections.list()
            all_collections = collections_response.collections

            if not all_collections:
                return "No collections found to survey."

            results = []
            total_matches = 0

            for coll in all_collections:
                try:
                    # Search this collection
                    search_response = self.client.collections.search(
                        collection_id=coll.collection_id,
                        query=query,
                        limit=self.mine_settings.get('multi_match_count', 5)
                    )

                    if search_response.results:
                        collection_results = []
                        for match in search_response.results:
                            if hasattr(match, 'chunk_content'):
                                preview = match.chunk_content[:self.mine_settings.get('match_preview_length', 200)]
                                if len(match.chunk_content) > self.mine_settings.get('match_preview_length', 200):
                                    preview += "..."
                                collection_results.append(f"  • {preview}")

                        if collection_results:
                            results.append(f"🏔️ {coll.collection_name}:")
                            results.extend(collection_results)
                            total_matches += len(collection_results)

                except Exception:
                    # Skip collections that fail to search
                    continue

            if not results:
                return f"No matches found for '{query}' across all collections."

            output = f"🔍 Survey Results for '{query}':\n"
            output += f"Found {total_matches} matches across {len([r for r in results if r.startswith('🏔️')])} collections\n\n"
            output += "\n".join(results)

            return output

        except Exception as e:
            return f"Error surveying collections: {e}"

    def _handle_dig(self, args: List[str]) -> str:
        """Dig up answers from active collection."""
        if not args:
            return "Usage: /mine --dig <question> [--to-drift <subgroup>]\n       /mine --dig -c <question>  # Search all collections\n       /mine --dig -h <question>  # Search with detailed output"

        # Parse flags from args
        use_all_collections = '-c' in args
        verbose_mode = '-h' in args

        # Remove flags from args to get the question
        question_args = [arg for arg in args if arg not in ['-c', '-h']]

        if not question_args:
            return "Usage: /mine --dig <question> [--to-drift <subgroup>]\n       /mine --dig -c <question>  # Search all collections\n       /mine --dig -h <question>  # Search with detailed output"

        question = " ".join(question_args)

        # Determine which collections to search
        if use_all_collections:
            # Get all collections
            try:
                collections_response = self.client.collections.list()
                collection_ids = [c.collection_id for c in collections_response.collections]
                if not collection_ids:
                    return "No collections found"
            except Exception as e:
                return f"Error listing collections: {e}"
        else:
            # Use active collection
            if not self.active_collection_id:
                return "No active collection. Use /mine use <name> first, or use -c to search all collections."
            collection_ids = [self.active_collection_id]

        try:
            # Load search configuration from both Isaac config and mine settings
            if self.session_manager:
                config = self.session_manager.get_config()
            else:
                config = {}
            xai_config = config.get('xai', {})
            collections_config = xai_config.get('collections', {})
            
            # Use mine_settings if available, fallback to main config
            search_files_only = self.mine_settings.get('search_files_only', collections_config.get('search_files_only', False))
            file_ids = self.mine_settings.get('file_ids', collections_config.get('file_ids', []))

            # Search the collection(s)
            # Note: xAI SDK has a hardcoded 10-second gRPC timeout for search operations
            # SDK returns multiple matches by default
            search_params = {
                'query': question,
                'collection_ids': collection_ids
            }
            
            # If searching specific files only, add file_ids filter
            if search_files_only and file_ids:
                # xAI SDK may support file filtering - add if available
                search_params['file_ids'] = file_ids
            
            response = self.client.collections.search(**search_params)

            if hasattr(response, 'matches') and response.matches:
                # Return top matches with truncated content for piping-friendly output
                # Collection chunks can be huge (user-configurable) - keep output manageable
                if verbose_mode:
                    # Verbose mode: show more matches and longer previews
                    max_matches = 5
                    max_chars = 3000  # for single match
                    max_preview = 1000  # for multiple matches
                else:
                    # Use config console settings
                    max_matches = self.mine_settings.get('multi_match_count', 5)
                    max_chars = self.mine_settings.get('max_chunk_size', 1000)
                    max_preview = self.mine_settings.get('match_preview_length', 200)
                
                matches = response.matches[:max_matches]  # Top matches
                
                if len(matches) == 1:
                    # Single match - return with moderate truncation
                    match = matches[0]
                    if hasattr(match, 'chunk_content'):
                        content = match.chunk_content
                        # Truncate very large chunks
                        if len(content) > max_chars:
                            content = content[:max_chars] + "\n... [content truncated]"
                        return f"Answer: {content}"
                    else:
                        return f"Found match: {match}"
                else:
                    # Multiple matches - return summary with previews
                    result = f"Found {len(response.matches)} matches"
                    if use_all_collections:
                        result += f" across {len(collection_ids)} collections"
                    result += ":\n\n"
                    
                    # Build collection name mapping for display
                    collection_names = {}
                    if use_all_collections:
                        try:
                            collections_response = self.client.collections.list()
                            for coll in collections_response.collections:
                                collection_names[coll.collection_id] = coll.collection_name
                        except Exception:
                            pass  # Fall back to IDs if name lookup fails
                    
                    for i, match in enumerate(matches, 1):
                        if hasattr(match, 'chunk_content'):
                            # Preview content
                            content = match.chunk_content[:max_preview]
                            if len(match.chunk_content) > max_preview:
                                content += "..."
                            
                            # Include score if available and enabled
                            score_text = ""
                            if self.mine_settings.get('show_scores', True):
                                score = getattr(match, 'score', None)
                                if score is not None:
                                    score_text = f" (score: {score:.3f})"
                            
                            # Include collection info for multi-collection searches
                            collection_info = ""
                            if use_all_collections and hasattr(match, 'collection_ids') and match.collection_ids:
                                coll_id = match.collection_ids[0]  # Take first collection ID
                                coll_name = collection_names.get(coll_id, coll_id)
                                collection_info = f" [{coll_name}]"
                            
                            result += f"Match {i}{score_text}{collection_info}:\n{content}\n\n"
                        else:
                            result += f"Match {i}: {match}\n\n"
                    return result.strip()
            else:
                search_scope = "all collections" if use_all_collections else "active collection"
                return f"No answer found in {search_scope}"
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
                    
                    # Get file_id for hauling
                    file_id = "unknown"
                    # Check common ID property names
                    for id_prop in ['file_id', 'id', 'document_id', 'fileId', 'documentId']:
                        if hasattr(doc, id_prop):
                            file_id = getattr(doc, id_prop)
                            break
                    
                    # Check nested file_metadata.file_id (protobuf structure)
                    if file_id == "unknown" and hasattr(doc, 'file_metadata') and doc.file_metadata:
                        if hasattr(doc.file_metadata, 'file_id'):
                            file_id = doc.file_metadata.file_id
                    
                    # If still unknown, try to inspect the object
                    if file_id == "unknown":
                        # Look for any property that looks like an ID
                        for attr_name in dir(doc):
                            if not attr_name.startswith('_'):
                                attr_value = getattr(doc, attr_name)
                                if isinstance(attr_value, str) and (attr_value.startswith('file_') or len(attr_value) == 36):
                                    file_id = attr_value
                                    break
                    
                    result += f"• {doc_name} (ID: {file_id})\n"
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
                
                # Check nested file_metadata.file_id (protobuf structure)
                if file_id == "unknown" and hasattr(doc, 'file_metadata') and doc.file_metadata:
                    if hasattr(doc.file_metadata, 'file_id'):
                        file_id = doc.file_metadata.file_id
                
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

    def _handle_drop(self, args: List[str]) -> str:
        """Drop file from collection (delete)."""
        if not args:
            return "Usage: /mine --drop <file_id>    # Delete file from collection"

        file_id = args[0]

        if not self.active_collection_id:
            return "No active collection. Use /mine --claim <name> first."

        try:
            # Find and delete the document
            documents_response = self.client.collections.list_documents(self.active_collection_id)
            documents = documents_response.documents

            target_doc = None
            filename = "Unknown"

            for doc in documents:
                # Check various possible ID fields
                doc_file_id = None
                for id_field in ['file_id', 'id', 'document_id', 'fileId', 'documentId']:
                    if hasattr(doc, id_field):
                        doc_file_id = getattr(doc, id_field)
                        break

                if doc_file_id == file_id:
                    target_doc = doc
                    # Get filename
                    if hasattr(doc, 'file_metadata') and getattr(doc, 'file_metadata'):
                        file_metadata = getattr(doc, 'file_metadata')
                        if hasattr(file_metadata, 'name'):
                            filename = getattr(file_metadata, 'name')
                    break

            if not target_doc:
                return f"File with ID '{file_id}' not found in active collection '{self.active_collection_name}'"

            # Delete the document
            # Note: xAI Collections API may not support deletion, this is a placeholder
            return f"⚠️  File deletion not implemented in current xAI Collections API\nFile: {filename} (ID: {file_id})\nCollection: {self.active_collection_name}"

        except Exception as e:
            return f"Error dropping file: {e}"

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
            except Exception:
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
            except Exception:
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
    try:
        # Read payload from stdin (dispatcher protocol)
        payload = json.loads(sys.stdin.read())
        args = payload.get("args", [])
        session_data = payload.get("session", {})
        
        # Create handler with session data
        handler = MineHandler(session_data)
        result = handler.handle_command(args, '/mine')
        
        # Return envelope
        print(json.dumps({
            "ok": True,
            "stdout": result
        }))
    
    except Exception as e:
        # Return error envelope
        print(json.dumps({
            "ok": False,
            "error": {
                "code": "EXECUTION_ERROR",
                "message": str(e)
            }
        }))


if __name__ == "__main__":
    main()