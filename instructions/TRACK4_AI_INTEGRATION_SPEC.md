# Track 4: AI Integration - Complete Implementation Specification

**Target:** Coding Agent (Implement)  
**Prerequisites:** ✅ Track 1.1 Complete (Dispatcher required for `/ask` command)  
**Estimated Time:** 8-10 hours  
**Complexity:** Medium-High  
**Priority:** High (reconnects AI query capability)

---

## Executive Summary

Reconnect and enhance Isaac's AI capabilities with three major features:
1. **`/ask` Command** - Direct AI chat (no command execution)
2. **Context-Aware AI** - Distinguish geographic queries from file lookups
3. **File History Integration** - Total Commander log ingestion for AI awareness

**Core Value:** Isaac becomes a true AI assistant, not just a command translator.

---

## Architecture Overview

### Three-Layer AI System

```
Layer 1: Direct AI Chat (/ask)
    ↓
Layer 2: Context-Aware Routing (geographic vs file vs shell)
    ↓
Layer 3: File History Awareness (Total Commander logs)
```

### Current AI Infrastructure (Already Exists)

**Available Components:**
- `isaac/ai/xai_client.py` - xAI/Grok API client ✅
- `isaac/ai/translator.py` - Natural language → shell command ✅
- `isaac/ai/validator.py` - Command safety validation ✅
- `isaac/ai/corrector.py` - Command typo correction ✅
- `isaac/ai/task_planner.py` - Multi-step task planning ✅

**What's Missing:**
- ❌ `/ask` command (direct chat mode)
- ❌ Context-aware query routing
- ❌ File history integration

---

## Phase 1: `/ask` Command - Direct AI Chat (3 hours)

### Problem Statement

**Current Behavior:**
```powershell
# User wants to ask a question
$> isaac where is alaska?
[AI translates to shell command, fails or gives weird result]
```

**Desired Behavior:**
```powershell
# Direct AI chat
$> /ask where is alaska?
Isaac> Alaska is in the far northwest of North America, 
       the largest U.S. state by area...

# No command execution, just conversation
$> /ask explain docker networking
Isaac> Docker networking allows containers to communicate...
```

### Two AI Modes Clarified

| Mode | Trigger | Behavior | Use Case |
|------|---------|----------|----------|
| **Translation** | `isaac <query>` | AI → shell command → execute | "list files", "what's my IP" |
| **Chat** | `/ask <query>` | AI → text response | "where is alaska?", "explain docker" |

### Implementation

#### File: `isaac/commands/ask/command.yaml`

```yaml
version: "1.0"
command:
  name: ask
  description: "Query AI for information (conversational, no command execution)"
  category: "ai"

triggers:
  - prefix: "/"
    pattern: "^ask\\s+(.+)$"
    capture: "query"

arguments:
  - name: query
    type: string
    required: true
    description: "Question or query for AI"

runtime:
  handler: "run.py"
  timeout_ms: 30000
  stdin: false

security:
  tier: 1
  resources:
    max_stdout_kib: 512
  capabilities:
    - network

examples:
  - "/ask where is alaska?"
  - "/ask what is warmer california or florida?"
  - "/ask explain docker networking"
```

#### File: `isaac/commands/ask/run.py`

```python
#!/usr/bin/env python3
"""
/ask command - Direct AI chat interface.

Unlike translation mode (isaac <query>), this sends queries directly to AI
and returns text responses without executing commands.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.ai.xai_client import XaiClient
from isaac.core.session_manager import SessionManager
from isaac.models.aiquery_history import AIQueryHistory

def main():
    try:
        # Load envelope
        envelope = json.load(sys.stdin) if not sys.stdin.isatty() else {}
        query = envelope.get('args', {}).get('query', '')
        
        if not query:
            print(json.dumps({
                "status": "error",
                "stderr": "Error: No query provided. Usage: /ask <question>"
            }))
            return
        
        # Get session and API key
        session = SessionManager.get_instance()
        api_key = session.preferences.get('xai_api_key')
        
        if not api_key:
            print(json.dumps({
                "status": "error",
                "stderr": "Error: xAI API key not configured. Use /config to set it."
            }))
            return
        
        # Initialize xAI client
        client = XaiClient(
            api_key=api_key,
            api_url=session.preferences.get('xai_api_url', 'https://api.x.ai/v1'),
            model=session.preferences.get('xai_model', 'grok-beta')
        )
        
        # Build chat preprompt (context-aware)
        preprompt = _build_chat_preprompt(session)
        
        # Query AI
        response = client.chat(
            prompt=query,
            system_prompt=preprompt
        )
        
        # Log query to AI history
        session.aiquery_history.log_query(
            query=query,
            response=response,
            mode='chat'
        )
        
        # Return response
        print(json.dumps({
            "status": "success",
            "stdout": response
        }))
    
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "stderr": f"Error querying AI: {e}"
        }))

def _build_chat_preprompt(session: SessionManager) -> str:
    """
    Build context-aware preprompt for chat mode.
    
    Includes:
    - System context (OS, shell, current directory)
    - User preferences
    - File history context (if available)
    """
    # Get system context
    shell_name = session.shell.name  # 'powershell' or 'bash'
    current_dir = Path.cwd()
    
    preprompt = f"""You are Isaac, an AI assistant integrated into the user's shell.

CONTEXT:
- Operating System: Windows (PowerShell)
- Current Shell: {shell_name}
- Current Directory: {current_dir}
- User: {session.preferences.get('username', 'unknown')}

IMPORTANT DISTINCTIONS:
1. Geographic/General Questions: Answer directly
   - "where is alaska?" → Geographic information
   - "what is docker?" → Technical explanation
   
2. File/Command Questions: Mention the command but don't execute
   - "where is alaska.exe?" → "You can search with: where.exe alaska.exe"
   - "show me my files" → "You can list files with: ls or dir"

3. Shell-Specific Awareness:
   - User is on {shell_name}, so reference appropriate commands
   - PowerShell: Get-*, Set-*, cmdlets
   - Bash: ls, grep, awk, sed

RESPONSE STYLE:
- Conversational and helpful
- Brief but complete answers
- Reference shell commands when relevant
- No command execution (this is chat mode)

Current user query follows below:
"""
    
    return preprompt

if __name__ == "__main__":
    main()
```

#### Integration: XaiClient Enhancement

**File:** `isaac/ai/xai_client.py` (add method)

```python
def chat(self, prompt: str, system_prompt: str = None) -> str:
    """
    Direct chat with AI (no command translation).
    
    Args:
        prompt: User query
        system_prompt: Optional system context
    
    Returns:
        AI response text
    """
    messages = []
    
    if system_prompt:
        messages.append({
            "role": "system",
            "content": system_prompt
        })
    
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    response = self._make_request(
        endpoint="chat/completions",
        data={
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024
        }
    )
    
    return response['choices'][0]['message']['content'].strip()
```

### Testing Phase 1

**Unit Tests:**
```python
# tests/test_ask_command.py

def test_ask_geographic_query():
    # /ask where is alaska?
    # Verify: Geographic answer, no command execution
    
def test_ask_technical_query():
    # /ask explain docker
    # Verify: Technical explanation
    
def test_ask_file_lookup_distinction():
    # /ask where is alaska.exe?
    # Verify: Suggests command, doesn't execute
```

**Manual Tests:**
```powershell
$> /ask where is alaska?
Isaac> Alaska is in the far northwest of North America...
✅ PASS

$> /ask what is docker?
Isaac> Docker is a containerization platform...
✅ PASS

$> /ask where is notepad.exe?
Isaac> You can search with: where.exe notepad.exe
✅ PASS (suggests command, doesn't execute)
```

### Success Criteria Phase 1

- ✅ `/ask` command plugin created
- ✅ Direct AI chat works (no command execution)
- ✅ Context-aware preprompt includes system info
- ✅ AI history logs chat queries
- ✅ Distinguishes geographic from file queries
- ✅ Shell-aware command suggestions

---

## Phase 2: Context-Aware Query Router (2 hours)

### Problem Statement

**Current Limitation:**
`/ask` requires explicit prefix. Users might forget and use `isaac` prefix.

**Desired Intelligence:**
```powershell
# Isaac should auto-detect intent
$> isaac where is alaska?
[AI detects: Geographic query → Chat mode]
Isaac> Alaska is in the far northwest of North America...

$> isaac where is alaska.exe?
[AI detects: File lookup → Translation mode]
Isaac> [translates to: where.exe alaska.exe]
[executes command]
```

### Implementation

#### File: `isaac/ai/query_classifier.py`

```python
"""
Query Classifier - Determine if query is geographic, file lookup, or shell command.

Uses heuristics + optional AI classification for edge cases.
"""
import re
from typing import Literal

QueryType = Literal['geographic', 'file_lookup', 'shell_command', 'general_info']

class QueryClassifier:
    """Classify natural language queries by intent."""
    
    # File extension patterns
    FILE_EXTENSIONS = r'\.(exe|dll|txt|log|csv|json|xml|py|js|md|bat|ps1|sh)$'
    
    # Geographic indicators
    GEOGRAPHIC_KEYWORDS = [
        'where is', 'location of', 'capital of', 'population of',
        'country', 'city', 'state', 'province', 'continent'
    ]
    
    # General info indicators
    INFO_KEYWORDS = [
        'what is', 'explain', 'how does', 'why does', 'tell me about',
        'define', 'describe', 'difference between'
    ]
    
    def classify(self, query: str) -> QueryType:
        """
        Classify query type.
        
        Args:
            query: Natural language query
        
        Returns:
            Query type classification
        """
        query_lower = query.lower().strip()
        
        # Check for file extensions (strong signal)
        if re.search(self.FILE_EXTENSIONS, query_lower):
            return 'file_lookup'
        
        # Check for file path patterns
        if self._looks_like_path(query):
            return 'file_lookup'
        
        # Check for geographic keywords
        if any(kw in query_lower for kw in self.GEOGRAPHIC_KEYWORDS):
            # But exclude if it ends with file extension
            if not re.search(self.FILE_EXTENSIONS, query_lower):
                return 'geographic'
        
        # Check for general info keywords
        if any(kw in query_lower for kw in self.INFO_KEYWORDS):
            return 'general_info'
        
        # Default: shell command translation
        return 'shell_command'
    
    def _looks_like_path(self, query: str) -> bool:
        """Check if query contains path-like patterns."""
        # Windows paths: C:\, \\server\, D:\
        if re.search(r'[A-Z]:\\|\\\\[\w-]+\\', query):
            return True
        
        # Unix paths: /usr/, ~/
        if re.search(r'^/[\w/]+|^~/[\w/]+', query):
            return True
        
        # Relative paths with slashes
        if '/' in query or '\\' in query:
            return True
        
        return False
```

#### Integration: CommandRouter Enhancement

**File:** `isaac/core/command_router.py` (update)

```python
from isaac.ai.query_classifier import QueryClassifier

class CommandRouter:
    def __init__(self):
        # Existing initialization...
        self.query_classifier = QueryClassifier()
    
    def route_natural_language(self, query: str, session: SessionManager) -> str:
        """
        Route natural language query intelligently.
        
        Classifies query intent and routes to appropriate handler:
        - Geographic/info: Direct chat (like /ask)
        - File lookup: Translation + execution
        - Shell command: Translation + execution
        """
        # Classify query
        query_type = self.query_classifier.classify(query)
        
        if query_type in ('geographic', 'general_info'):
            # Route to chat mode (same as /ask)
            return self._handle_chat_query(query, session)
        else:
            # Route to translation mode (existing behavior)
            return self._handle_translation_query(query, session)
    
    def _handle_chat_query(self, query: str, session: SessionManager) -> str:
        """Handle chat-style query (no execution)."""
        # Use same logic as /ask command
        from isaac.ai.xai_client import XaiClient
        
        client = XaiClient(...)
        preprompt = self._build_chat_preprompt(session)
        response = client.chat(query, preprompt)
        
        # Log to AI history
        session.aiquery_history.log_query(
            query=query,
            response=response,
            mode='chat_auto'  # Auto-detected chat
        )
        
        return response
    
    def _handle_translation_query(self, query: str, session: SessionManager) -> str:
        """Handle translation query (existing behavior)."""
        # Existing translation logic...
        pass
```

### Testing Phase 2

**Classification Tests:**
```python
# tests/test_query_classifier.py

def test_classify_geographic():
    assert classifier.classify("where is alaska?") == "geographic"
    assert classifier.classify("capital of france") == "geographic"

def test_classify_file_lookup():
    assert classifier.classify("where is alaska.exe?") == "file_lookup"
    assert classifier.classify("find notepad.exe") == "file_lookup"

def test_classify_shell_command():
    assert classifier.classify("list files") == "shell_command"
    assert classifier.classify("show processes") == "shell_command"

def test_classify_general_info():
    assert classifier.classify("what is docker?") == "general_info"
    assert classifier.classify("explain kubernetes") == "general_info"
```

**Integration Tests:**
```python
def test_auto_route_geographic():
    # isaac where is alaska?
    # Should route to chat mode, not translate
    
def test_auto_route_file_lookup():
    # isaac where is alaska.exe?
    # Should translate and execute
```

### Success Criteria Phase 2

- ✅ QueryClassifier correctly identifies query types
- ✅ Geographic queries auto-route to chat mode
- ✅ File lookups auto-route to translation mode
- ✅ Edge cases handled (alaska vs alaska.exe)
- ✅ AI history tracks auto-detected mode

---

## Phase 3: File History Integration (4-5 hours)

### Problem Statement

**Current Gap:**
AI has no awareness of user's file management history.

**User Need:**
"Where did I move project X?"
"I made redundant copies of Y, can you help me clean up?"

**Solution:**
Ingest Total Commander logs into xAI vector collections for AI context.

### Total Commander Log Format

**Example Log (WINCMD.LOG):**
```
2025-10-20 14:23:15 Copy: C:\Projects\Isaac\backup.zip -> D:\Backups\2025-10-20\
2025-10-20 14:25:03 Move: C:\Downloads\data.csv -> C:\Projects\Analysis\raw_data\
2025-10-20 14:30:12 Delete: C:\Temp\old_stuff\
2025-10-20 15:10:45 Copy: C:\Projects\Isaac\isaac.exe -> D:\Archive\isaac-v1.0.exe
```

### Architecture

```
Total Commander (WINCMD.LOG)
    ↓
Parser (totalcmd_parser.py) → Extract operations
    ↓
Collection Manager (xai_collections.py) → Upload to xAI
    ↓
Scheduler (background cron) → Periodic sync
    ↓
AI Context (preprompt injection) → Query on /ask
```

### Implementation: Step 1 - Log Parser

**File:** `isaac/integrations/totalcmd_parser.py`

```python
"""
Total Commander log parser.
Extracts file operations from WINCMD.LOG format.
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TotalCommanderParser:
    """Parse Total Commander operation logs."""
    
    def __init__(self, log_path: Path):
        """
        Initialize parser.
        
        Args:
            log_path: Path to WINCMD.LOG file
        """
        self.log_path = log_path
        self.last_parsed_position = 0  # Byte offset for incremental parsing
    
    def parse_log(self, incremental: bool = True) -> List[Dict]:
        """
        Parse Total Commander log file.
        
        Args:
            incremental: Only parse new entries since last parse
        
        Returns:
            List of operation dicts
        """
        if not self.log_path.exists():
            logger.warning(f"Log file not found: {self.log_path}")
            return []
        
        operations = []
        
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='ignore') as f:
                if incremental:
                    # Seek to last position
                    f.seek(self.last_parsed_position)
                
                for line in f:
                    op = self._parse_line(line.strip())
                    if op:
                        operations.append(op)
                
                # Update position
                self.last_parsed_position = f.tell()
        
        except Exception as e:
            logger.error(f"Error parsing log: {e}")
        
        return operations
    
    def _parse_line(self, line: str) -> Optional[Dict]:
        """
        Parse single log line.
        
        Format: YYYY-MM-DD HH:MM:SS Operation: source -> destination
        """
        # Pattern for copy/move operations
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) (Copy|Move|Delete|Rename): (.+?)( -> (.+))?$'
        match = re.match(pattern, line, re.IGNORECASE)
        
        if not match:
            return None
        
        timestamp_str, operation, source, _, destination = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        
        return {
            "timestamp": timestamp.isoformat(),
            "operation": operation.lower(),
            "source": source.strip(),
            "destination": destination.strip() if destination else None,
            "raw_line": line
        }
    
    def get_operations_since(self, since: datetime) -> List[Dict]:
        """Get operations since specific timestamp."""
        all_ops = self.parse_log(incremental=False)
        return [
            op for op in all_ops
            if datetime.fromisoformat(op['timestamp']) >= since
        ]
```

### Implementation: Step 2 - xAI Collection Manager

**File:** `isaac/integrations/xai_collections.py`

```python
"""
xAI Vector Collection Manager for file history.
"""
import logging
from typing import List, Dict
from isaac.ai.xai_client import XaiClient

logger = logging.getLogger(__name__)

class FileHistoryCollectionManager:
    """Manage file history in xAI vector collections."""
    
    COLLECTION_NAME = "isaac_file_history"
    
    def __init__(self, xai_client: XaiClient):
        """
        Initialize collection manager.
        
        Args:
            xai_client: Configured XaiClient instance
        """
        self.client = xai_client
        self._ensure_collection_exists()
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            # Check if collection exists
            collections = self.client.list_collections()
            if self.COLLECTION_NAME not in collections:
                self.client.create_collection(
                    name=self.COLLECTION_NAME,
                    description="File operation history from Total Commander"
                )
                logger.info(f"Created collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
    
    def upload_operations(self, operations: List[Dict]) -> int:
        """
        Upload file operations to collection.
        
        Args:
            operations: List of operation dicts from parser
        
        Returns:
            Number of operations uploaded
        """
        if not operations:
            return 0
        
        # Convert operations to searchable text documents
        documents = [self._operation_to_document(op) for op in operations]
        
        try:
            self.client.add_documents(
                collection=self.COLLECTION_NAME,
                documents=documents
            )
            logger.info(f"Uploaded {len(operations)} operations to collection")
            return len(operations)
        
        except Exception as e:
            logger.error(f"Error uploading operations: {e}")
            return 0
    
    def _operation_to_document(self, operation: Dict) -> Dict:
        """
        Convert operation dict to searchable document.
        
        Format optimized for semantic search.
        """
        op_type = operation['operation']
        source = operation['source']
        dest = operation.get('destination', '')
        timestamp = operation['timestamp']
        
        # Build searchable text
        if op_type == 'delete':
            text = f"Deleted {source} on {timestamp}"
        elif op_type in ('copy', 'move'):
            text = f"{op_type.title()}d {source} to {dest} on {timestamp}"
        else:
            text = operation['raw_line']
        
        return {
            "id": f"{timestamp}_{op_type}_{hash(source)}",
            "text": text,
            "metadata": operation
        }
    
    def query_file_history(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Query file history by natural language.
        
        Args:
            query: Natural language query
            limit: Max results to return
        
        Returns:
            List of matching operations
        """
        try:
            results = self.client.search_collection(
                collection=self.COLLECTION_NAME,
                query=query,
                limit=limit
            )
            return [r['metadata'] for r in results]
        
        except Exception as e:
            logger.error(f"Error querying file history: {e}")
            return []
```

### Implementation: Step 3 - Background Scheduler

**File:** `isaac/scheduler/cron_manager.py`

```python
"""
Background task scheduler for periodic jobs.
"""
import threading
import time
import logging
from typing import Callable, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CronManager:
    """Simple cron-like scheduler for background tasks."""
    
    def __init__(self):
        self.tasks: Dict[str, Dict] = {}
        self.running = False
        self._thread = None
    
    def register_task(self, name: str, func: Callable, 
                      interval_minutes: int, run_immediately: bool = False):
        """
        Register periodic task.
        
        Args:
            name: Unique task name
            func: Callable to execute
            interval_minutes: Run every N minutes
            run_immediately: Run on registration
        """
        self.tasks[name] = {
            "func": func,
            "interval": timedelta(minutes=interval_minutes),
            "last_run": None if not run_immediately else datetime.now(),
            "next_run": datetime.now() if run_immediately else 
                        datetime.now() + timedelta(minutes=interval_minutes)
        }
        logger.info(f"Registered task: {name} (every {interval_minutes}m)")
    
    def start(self):
        """Start scheduler thread."""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Cron manager started")
    
    def stop(self):
        """Stop scheduler gracefully."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Cron manager stopped")
    
    def _run_loop(self):
        """Main scheduler loop."""
        while self.running:
            now = datetime.now()
            
            for task_name, task in self.tasks.items():
                if now >= task['next_run']:
                    try:
                        logger.debug(f"Running task: {task_name}")
                        task['func']()
                        task['last_run'] = now
                        task['next_run'] = now + task['interval']
                    except Exception as e:
                        logger.error(f"Task {task_name} failed: {e}")
            
            # Check every 60 seconds
            time.sleep(60)
```

### Implementation: Step 4 - Integration

**File:** `isaac/core/session_manager.py` (add)

```python
from isaac.integrations.totalcmd_parser import TotalCommanderParser
from isaac.integrations.xai_collections import FileHistoryCollectionManager
from isaac.scheduler.cron_manager import CronManager

class SessionManager:
    def __init__(self, ...):
        # Existing initialization...
        
        # File history integration
        self.totalcmd_parser = None
        self.file_history_manager = None
        self.cron_manager = CronManager()
        
        # Initialize if Total Commander log exists
        self._init_file_history()
        
        # Start background scheduler
        self.cron_manager.start()
    
    def _init_file_history(self):
        """Initialize Total Commander log integration."""
        # Default log path (configurable via preferences)
        log_path = Path(self.preferences.get(
            'totalcmd_log_path',
            r'C:\Program Files\Total Commander\WINCMD.LOG'
        ))
        
        if not log_path.exists():
            logger.info("Total Commander log not found, skipping file history")
            return
        
        # Initialize parser
        self.totalcmd_parser = TotalCommanderParser(log_path)
        
        # Initialize collection manager
        if self.preferences.get('xai_api_key'):
            self.file_history_manager = FileHistoryCollectionManager(
                xai_client=self.xai_client
            )
            
            # Register periodic upload task
            upload_interval = self.preferences.get('file_history_upload_interval', 60)  # minutes
            self.cron_manager.register_task(
                name='upload_file_history',
                func=self._upload_file_history,
                interval_minutes=upload_interval,
                run_immediately=False
            )
            logger.info(f"File history sync enabled (every {upload_interval}m)")
    
    def _upload_file_history(self):
        """Background task: Parse and upload new file operations."""
        if not self.totalcmd_parser or not self.file_history_manager:
            return
        
        try:
            # Parse new operations (incremental)
            operations = self.totalcmd_parser.parse_log(incremental=True)
            
            if operations:
                # Upload to xAI collection
                count = self.file_history_manager.upload_operations(operations)
                logger.info(f"Synced {count} file operations to AI collection")
        
        except Exception as e:
            logger.error(f"File history upload failed: {e}")
    
    def shutdown(self):
        """Graceful shutdown."""
        # Stop scheduler
        if hasattr(self, 'cron_manager'):
            self.cron_manager.stop()
        
        # Existing shutdown logic...
```

### Implementation: Step 5 - AI Context Enhancement

**Update `/ask` preprompt to query file history:**

```python
def _build_chat_preprompt(session: SessionManager) -> str:
    """Build context-aware preprompt with file history."""
    
    # Base preprompt (existing)
    preprompt = """You are Isaac, an AI assistant..."""
    
    # Add file history context if available
    if session.file_history_manager:
        # Check if query is file-related
        # If so, query recent file operations
        try:
            recent_ops = session.file_history_manager.query_file_history(
                query="recent file moves and copies",
                limit=20
            )
            
            if recent_ops:
                preprompt += "\n\nRECENT FILE OPERATIONS:\n"
                for op in recent_ops[:10]:  # Limit to 10 for context size
                    preprompt += f"- {op['timestamp']}: {op['operation']} {op['source']}"
                    if op.get('destination'):
                        preprompt += f" -> {op['destination']}"
                    preprompt += "\n"
        except Exception as e:
            logger.debug(f"Could not fetch file history: {e}")
    
    return preprompt
```

### Testing Phase 3

**Parser Tests:**
```python
def test_parse_totalcmd_log():
    # Parse sample log
    # Verify operations extracted
    
def test_incremental_parsing():
    # Parse, add new lines, parse again
    # Verify only new operations returned
```

**Collection Tests:**
```python
def test_upload_operations():
    # Mock xAI client
    # Upload operations
    # Verify API called correctly
    
def test_query_file_history():
    # Mock collection with operations
    # Query "where did I move isaac?"
    # Verify relevant results returned
```

**Integration Tests:**
```python
def test_file_history_in_ask():
    # /ask where did I move my backup?
    # Verify: AI response references file history
```

### Success Criteria Phase 3

- ✅ Total Commander log parser working
- ✅ Incremental parsing (only new entries)
- ✅ xAI collection manager uploads operations
- ✅ Background cron scheduler runs tasks
- ✅ SessionManager initializes file history
- ✅ `/ask` preprompt includes file context
- ✅ AI can answer "where did I move X?"
- ✅ Graceful degradation if log not found

---

## Configuration

### User Preferences (add to SessionManager)

```json
{
  "xai_api_key": "xai-...",
  "xai_api_url": "https://api.x.ai/v1",
  "xai_model": "grok-beta",
  "totalcmd_log_path": "C:\\Program Files\\Total Commander\\WINCMD.LOG",
  "file_history_enabled": true,
  "file_history_upload_interval": 60
}
```

### Configuration Commands

```powershell
# Enable file history
$> /config set file_history_enabled true

# Set log path
$> /config set totalcmd_log_path "C:\TC\WINCMD.LOG"

# Set upload interval (minutes)
$> /config set file_history_upload_interval 30

# Manual sync
$> /sync-file-history
```

---

## Testing Strategy

### Unit Tests (3 hours)

**Test Files:**
- `tests/test_ask_command.py` - `/ask` command functionality
- `tests/test_query_classifier.py` - Intent classification
- `tests/test_totalcmd_parser.py` - Log parsing
- `tests/test_xai_collections.py` - Collection management
- `tests/test_cron_manager.py` - Scheduler

### Integration Tests (2 hours)

**Test Files:**
- `tests/test_ai_integration.py` - End-to-end AI flows
- `tests/test_file_history_integration.py` - File history in AI context

### Manual Testing Scenarios

**Phase 1: `/ask` Command**
```powershell
$> /ask where is alaska?
✅ Geographic answer (no command)

$> /ask what is docker?
✅ Technical explanation

$> /ask where is notepad.exe?
✅ Suggests command, doesn't execute
```

**Phase 2: Auto-Routing**
```powershell
$> isaac where is alaska?
✅ Routes to chat mode

$> isaac where is alaska.exe?
✅ Routes to translation mode
```

**Phase 3: File History**
```powershell
$> /ask where did I move isaac-backup?
✅ AI references file history from Total Commander logs

$> /ask I made redundant copies of project X
✅ AI lists duplicate file operations
```

---

## Success Criteria (Overall)

### Phase 1: `/ask` Command
- ✅ `/ask` command plugin created
- ✅ Direct AI chat works (no execution)
- ✅ Context-aware preprompt
- ✅ AI history logging
- ✅ Geographic vs file distinction

### Phase 2: Context-Aware Routing
- ✅ QueryClassifier implemented
- ✅ Auto-routing based on intent
- ✅ Edge cases handled correctly

### Phase 3: File History
- ✅ Total Commander parser working
- ✅ xAI collection uploads
- ✅ Background scheduler operational
- ✅ AI context includes file history
- ✅ Natural language file queries work

---

## Implementation Timeline

| Phase | Component | Time | Dependencies |
|-------|-----------|------|--------------|
| **1** | `/ask` command plugin | 2h | Track 1.1 (dispatcher) |
| **1** | XaiClient.chat() method | 1h | Existing xai_client.py |
| **2** | QueryClassifier | 1h | None |
| **2** | CommandRouter enhancement | 1h | QueryClassifier |
| **3** | TotalCommanderParser | 1.5h | None |
| **3** | FileHistoryCollectionManager | 1.5h | XaiClient |
| **3** | CronManager scheduler | 1h | None |
| **3** | SessionManager integration | 1h | All Phase 3 components |
| **Testing** | Unit + integration tests | 3h | All phases |
| **Total** | | **12 hours** | |

**Note:** Estimate is 12 hours (includes buffer). Core implementation: 8-10 hours.

---

## Dependencies

### Python Packages (existing)
- ✅ `requests` - xAI API calls
- ✅ `json` - Envelope I/O
- ✅ `threading` - Background scheduler
- ✅ `pathlib` - File operations
- ✅ `re` - Log parsing

### Isaac Components
- ✅ `XaiClient` - Already exists
- ✅ `SessionManager` - Extend with file history
- ✅ `CommandRouter` - Enhance with query classification
- ✅ `Dispatcher` - Required for `/ask` command

### External Services
- xAI API (Grok) - Already configured
- xAI Vector Collections - Requires API access

---

## Error Handling

### API Failures
```python
# Graceful degradation
try:
    response = client.chat(query)
except APIError:
    return "AI service temporarily unavailable. Try again later."
```

### Missing Log File
```python
# Don't fail startup
if not log_path.exists():
    logger.info("Total Commander log not found, file history disabled")
    return  # Continue without file history
```

### Collection Upload Failures
```python
# Retry with exponential backoff
# Log error but don't crash
# User can manually trigger /sync-file-history
```

---

## Future Enhancements (Post-Track 4)

1. **Multi-Log Support:**
   - Ingest from multiple sources (Git logs, shell history, etc.)
   - Unified file operation timeline

2. **Smart Cleanup Suggestions:**
   - Detect redundant copies automatically
   - Suggest deletions with confirmation

3. **File Relationship Graph:**
   - Track file ancestry (copy chains)
   - Visualize file movement over time

4. **Advanced Query Types:**
   - "Show all files moved to D: in October"
   - "Find all copies of project X"
   - "What did I delete yesterday?"

5. **Multi-Provider AI:**
   - Support Claude, GPT-4, Gemini for chat mode
   - Fallback if xAI unavailable

---

## Handoff Notes for Coding Agent

**Start with Phase 1:**
1. Create `/ask` command plugin (YAML + run.py)
2. Add `chat()` method to XaiClient
3. Test basic chat functionality
4. Verify no command execution in chat mode

**Then Phase 2:**
1. Implement QueryClassifier (heuristics first)
2. Enhance CommandRouter with auto-routing
3. Test edge cases (alaska vs alaska.exe)

**Finally Phase 3:**
1. Build TotalCommanderParser (test with sample log)
2. Implement FileHistoryCollectionManager
3. Add CronManager scheduler
4. Integrate into SessionManager
5. Test end-to-end with real Total Commander logs

**Testing Priority:**
- Phase 1 tests critical (chat vs execution distinction)
- Phase 2 tests important (classification accuracy)
- Phase 3 tests nice-to-have (graceful degradation)

---

**Specification complete. Ready for implementation.**
