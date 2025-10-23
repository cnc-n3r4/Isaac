# Isaac Sandbox & Workspace System

## Problem Statement
Isaac needs to:
1. **Learn** environment isolation (venv, containers, filesystem restrictions)
2. **Protect** the system from dangerous operations (root stuff, system dirs)
3. **Enable** other bots to work safely in isolated workspaces
4. **Manage** credentials and access keys for bot ecosystem

**User's goal:** "from what i learn from that, learn how to build out workspaces. and isaac can be the bot that scaffolds them out, etc. has the 'key's so that my other bots can build projects"

## Phase 1: Sandbox Settings in Config Console

### New Config Section
Add to `isaac/ui/config_console.py`:

```python
SANDBOX_SETTINGS = [
    {
        "key": "sandbox.enabled",
        "type": "bool",
        "default": False,
        "description": "Restrict Isaac to safe operations only"
    },
    {
        "key": "sandbox.root_dir",
        "type": "path",
        "default": "~/.isaac/sandboxes",
        "description": "Base directory for isolated environments"
    },
    {
        "key": "sandbox.block_system_paths",
        "type": "bool",
        "default": True,
        "description": "Prevent access to /etc, /sys, C:\\Windows, etc."
    },
    {
        "key": "sandbox.max_file_size_mb",
        "type": "int",
        "default": 100,
        "description": "Maximum file size for operations"
    },
    {
        "key": "sandbox.allowed_commands",
        "type": "list",
        "default": ["pip", "npm", "git", "python", "node"],
        "description": "Whitelist of allowed shell commands in sandbox"
    }
]
```

### Config Console Layout Update
```
┌─ ISAAC 2.0 Configuration ────────────────────────────────┐
│  [Collections] [Piping] [Sandbox] [Advanced]  <-- Tabs  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Sandbox Settings                                         │
│  ─────────────────                                        │
│                                                           │
│  Enable Sandbox Mode:         [X] Yes  [ ] No           │
│  Sandbox Root Directory:      ~/.isaac/sandboxes         │
│  Block System Directories:    [X] Yes  [ ] No           │
│  Max File Size (MB):          [100              ]        │
│  Allowed Commands:            pip, npm, git, python      │
│                                                           │
│  ⚠ Sandbox mode restricts dangerous operations          │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## Phase 2: Sandbox Enforcement System

### File: `isaac/core/sandbox.py`

```python
"""
Sandbox enforcement for safe operations
Inspired by Joshua (WarGames) - "The only winning move is not to play"
"""

from pathlib import Path
import os
import platform

class SandboxViolation(Exception):
    """Raised when operation violates sandbox rules"""
    pass

class Sandbox:
    """Enforce safety boundaries for Isaac operations"""
    
    # System paths that should never be modified
    WINDOWS_PROTECTED = [
        "C:\\Windows", "C:\\Program Files", "C:\\Program Files (x86)",
        "C:\\ProgramData", "C:\\Users\\All Users"
    ]
    
    UNIX_PROTECTED = [
        "/etc", "/sys", "/proc", "/boot", "/bin", "/sbin", "/usr/bin", 
        "/usr/sbin", "/lib", "/lib64", "/dev"
    ]
    
    def __init__(self, config: dict):
        self.enabled = config.get("sandbox.enabled", False)
        self.root_dir = Path(config.get("sandbox.root_dir", "~/.isaac/sandboxes")).expanduser()
        self.block_system = config.get("sandbox.block_system_paths", True)
        self.max_file_size = config.get("sandbox.max_file_size_mb", 100) * 1024 * 1024  # bytes
        self.allowed_cmds = config.get("sandbox.allowed_commands", ["pip", "npm", "git"])
        
        # Create sandbox root if needed
        if self.enabled:
            self.root_dir.mkdir(parents=True, exist_ok=True)
    
    def check_path(self, path: Path) -> None:
        """Verify path is safe to access
        
        Raises:
            SandboxViolation: If path is protected
        """
        if not self.enabled:
            return
        
        path = Path(path).resolve()
        
        # Check against protected system paths
        if self.block_system:
            protected = self.WINDOWS_PROTECTED if platform.system() == "Windows" else self.UNIX_PROTECTED
            
            for protected_path in protected:
                if path.is_relative_to(Path(protected_path)):
                    raise SandboxViolation(
                        f"Access denied: {path} is in protected system directory {protected_path}"
                    )
    
    def check_command(self, command: str) -> None:
        """Verify command is allowed in sandbox
        
        Raises:
            SandboxViolation: If command is not whitelisted
        """
        if not self.enabled:
            return
        
        # Extract base command (first word)
        cmd_base = command.strip().split()[0]
        
        if cmd_base not in self.allowed_cmds:
            raise SandboxViolation(
                f"Command '{cmd_base}' not allowed in sandbox. Allowed: {', '.join(self.allowed_cmds)}"
            )
    
    def check_file_size(self, filepath: Path) -> None:
        """Verify file size is within limits
        
        Raises:
            SandboxViolation: If file exceeds max size
        """
        if not self.enabled:
            return
        
        if filepath.exists():
            size = filepath.stat().st_size
            if size > self.max_file_size:
                raise SandboxViolation(
                    f"File {filepath} ({size / 1024 / 1024:.1f}MB) exceeds limit ({self.max_file_size / 1024 / 1024}MB)"
                )
```

### Integration with Command Router

**File:** `isaac/core/command_router.py`

```python
from isaac.core.sandbox import Sandbox, SandboxViolation

class CommandRouter:
    def __init__(self, session_manager: SessionManager):
        self.session = session_manager
        self.sandbox = Sandbox(session_manager.config)
    
    def route_command(self, command: str) -> CommandResult:
        """Route command through safety checks"""
        
        # Sandbox pre-check
        try:
            self.sandbox.check_command(command)
        except SandboxViolation as e:
            return CommandResult(
                success=False,
                output=f"🛑 Sandbox violation: {e}",
                exit_code=1
            )
        
        # ... rest of routing logic
```

## Phase 3: Workspace Management System

### File: `isaac/core/workspace_manager.py`

```python
"""
Workspace scaffolding and credential management
Isaac creates isolated environments for other bots
"""

from pathlib import Path
import subprocess
import json
import secrets

class WorkspaceManager:
    """Create and manage isolated workspaces for bots"""
    
    def __init__(self, config: dict, sandbox: Sandbox):
        self.config = config
        self.sandbox = sandbox
        self.workspace_dir = Path(config.get("workspace_dir", "~/Projects/isaac-ws")).expanduser()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Key store for bot credentials
        self.keystore_path = self.workspace_dir / ".keystore.json"
        self.keys = self._load_keys()
    
    def create_workspace(self, name: str, python_version: str = None, 
                        node_version: str = None, isolated: bool = True) -> dict:
        """Create isolated workspace with environment
        
        Args:
            name: Workspace identifier
            python_version: Python version (e.g., "3.11")
            node_version: Node version (e.g., "18")
            isolated: Use venv/nvm isolation
        
        Returns:
            Workspace metadata dict with paths and credentials
        """
        ws_path = self.workspace_dir / name
        ws_path.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "name": name,
            "path": str(ws_path),
            "created": datetime.now().isoformat(),
            "isolated": isolated,
            "access_key": secrets.token_urlsafe(32)
        }
        
        # Create Python venv if requested
        if python_version:
            venv_path = ws_path / ".venv"
            python_cmd = f"python{python_version}" if python_version else "python"
            subprocess.run([python_cmd, "-m", "venv", str(venv_path)], check=True)
            metadata["python_venv"] = str(venv_path)
        
        # Create Node environment if requested
        if node_version:
            # Use nvm or nodeenv
            metadata["node_version"] = node_version
        
        # Save metadata
        (ws_path / ".workspace.json").write_text(json.dumps(metadata, indent=2))
        
        # Store key
        self.keys[name] = metadata["access_key"]
        self._save_keys()
        
        return metadata
    
    def grant_access(self, workspace: str, bot_name: str, 
                    permissions: list[str]) -> str:
        """Grant bot access to workspace
        
        Args:
            workspace: Workspace name
            bot_name: Bot identifier
            permissions: List of permissions (e.g., ["read", "write", "execute"])
        
        Returns:
            Access token for bot
        """
        ws_path = self.workspace_dir / workspace
        if not ws_path.exists():
            raise ValueError(f"Workspace '{workspace}' not found")
        
        # Generate bot-specific token
        token = secrets.token_urlsafe(32)
        
        # Save grant metadata
        grants_path = ws_path / ".grants.json"
        grants = json.loads(grants_path.read_text()) if grants_path.exists() else {}
        grants[bot_name] = {
            "token": token,
            "permissions": permissions,
            "granted": datetime.now().isoformat()
        }
        grants_path.write_text(json.dumps(grants, indent=2))
        
        return token
    
    def verify_access(self, workspace: str, token: str) -> bool:
        """Verify bot has access to workspace"""
        ws_path = self.workspace_dir / workspace
        grants_path = ws_path / ".grants.json"
        
        if not grants_path.exists():
            return False
        
        grants = json.loads(grants_path.read_text())
        return any(g["token"] == token for g in grants.values())
    
    def cleanup(self, workspace: str):
        """Remove workspace and revoke all access"""
        ws_path = self.workspace_dir / workspace
        if ws_path.exists():
            shutil.rmtree(ws_path)
        
        # Remove from keystore
        if workspace in self.keys:
            del self.keys[workspace]
            self._save_keys()
    
    def _load_keys(self) -> dict:
        """Load key store"""
        if self.keystore_path.exists():
            return json.loads(self.keystore_path.read_text())
        return {}
    
    def _save_keys(self):
        """Save key store"""
        self.keystore_path.write_text(json.dumps(self.keys, indent=2))
```

## Phase 4: @workspace - Internal Project Context Manager

### The @ Prefix for Internal Commands

Isaac uses clean namespace separation:
- `!bang` = External routing (Telegram, webhooks, bots)
- `@internal` = Internal system commands (workspace, sandbox, sync, debug)
- `/command` = User-facing Isaac commands
- `$shell` = Direct shell pass-through (future)

### @workspace Commands

```bash
# Set active workspace (affects all /projio commands)
@workspace set ~/Projects/my-web-app
@workspace set my-web-app  # Fuzzy match from history

# SHORTCUT: @<workspace-name> = @workspace set <name>
@my-web-app                # Quick switch!
@big-pharma-web-job        # Jump to workspace
@jimbobs-project           # No typing "@workspace set"

# Switch workspace
@workspace switch big-pharma-web-job
@workspace back    # Previous workspace (like cd -)
@workspace forward # Next in history

# Workspace info
@workspace info           # Current workspace details
@workspace list           # All workspaces
@workspace history        # Recent workspaces

# Change shell CWD to workspace root
@workspace cd

# Workspace state management
@workspace snapshot              # Save state (CWD, env, git branch)
@workspace restore <snapshot>    # Restore saved state
@workspace export                # Export as blob (pipeable!)
@workspace import <blob>         # Import someone else's workspace

# Multi-terminal coordination
@workspace lock                  # Lock workspace (prevent other terminals)
@workspace unlock                # Release lock
@workspace takeover              # Force-take from other terminal
@workspace status                # Show lock status, active terminal

# Workspace creation/cleanup (bot-focused)
@workspace create my-bot-project --python 3.11 --isolated
@workspace grant code-bot --permissions read,write
@workspace cleanup --older-than 7d
@workspace archive client-old-project
```

### Integration with /projio

**Before @workspace (explicit project selection):**
```bash
/projio send -pro "big-pharma-web-job" | /mine cast
/projio skeleton -pro "my-web-app" | /ask "what's missing?"
/projio deps scan -pro "client-widget"
```

**With @workspace (implicit context):**
```bash
@workspace set big-pharma-web-job
/projio send | /mine cast             # Uses active workspace
/projio skeleton | /ask "review"      # No -pro flag needed
/projio deps scan                     # Context-aware

# Or one-liner:
@workspace with big-pharma-web-job /projio send | /mine cast
```

### Cloud-Synced Workspace State

**File:** Cloud-synced `workspaces.json`

```json
{
  "active_workspace": "big-pharma-web-job",
  "workspaces": [
    {
      "id": "ws_abc123",
      "name": "big-pharma-web-job",
      "path": "C:\\Projects\\big-pharma-web-job",
      "type": "user",  // user, bot, temporary
      "created": "2025-10-01T10:00:00Z",
      "last_accessed": "2025-10-22T14:30:00Z",
      "last_terminal": "laptop_001",
      "locked_by": null,
      "git_branch": "feature-auth",
      "git_dirty": false,
      "env_vars": {
        "NODE_ENV": "development",
        "PYTHON_VERSION": "3.11"
      },
      "resources": {
        "disk_mb": 450,
        "file_count": 247
      },
      "snapshots": [
        {
          "id": "snap_001",
          "timestamp": "2025-10-22T12:00:00Z",
          "cwd": "C:\\Projects\\big-pharma-web-job\\src",
          "git_branch": "main",
          "description": "Before refactor"
        }
      ]
    },
    {
      "id": "ws_xyz789",
      "name": "my-web-app",
      "path": "~/Projects/my-web-app",
      "type": "user",
      "created": "2025-09-15T08:00:00Z",
      "last_accessed": "2025-10-22T10:15:00Z",
      "last_terminal": "desktop_002",
      "locked_by": "desktop_002",
      "lock_expires": "2025-10-22T16:00:00Z"
    }
  ],
  "history": [
    "big-pharma-web-job",
    "my-web-app",
    "client-widget",
    "test-project"
  ],
  "bot_workspaces": [
    {
      "id": "ws_bot_001",
      "name": "code-bot-temp-1234",
      "path": "~/.isaac/workspaces/code-bot-temp-1234",
      "type": "bot",
      "created_by_bot": "code-generator-v1",
      "expires": "2025-10-23T14:30:00Z",
      "auto_cleanup": true
    }
  ]
}
```

### @workspace Class Implementation

**File:** `isaac/core/workspace_context.py`

```python
"""
@workspace - Internal project context management
Sets active workspace for all /projio operations
"""

from pathlib import Path
from datetime import datetime, timedelta
import json

class WorkspaceContext:
    """Manage active workspace context for Isaac"""
    
    def __init__(self, cloud_client, session_manager):
        self.cloud = cloud_client
        self.session = session_manager
        self.terminal_id = session_manager.terminal_id
    
    def set_workspace(self, identifier: str) -> dict:
        """Set active workspace
        
        Args:
            identifier: Workspace name or path (fuzzy matched)
        
        Returns:
            Workspace metadata dict
        """
        workspaces_data = self.cloud.get("workspaces.json")
        
        # Fuzzy match from history/name/path
        workspace = self._find_workspace(identifier, workspaces_data)
        if not workspace:
            raise ValueError(f"Workspace '{identifier}' not found")
        
        # Check if locked by other terminal
        if workspace.get("locked_by") and workspace["locked_by"] != self.terminal_id:
            lock_time = datetime.fromisoformat(workspace["lock_expires"])
            if datetime.now() < lock_time:
                raise ValueError(
                    f"Workspace locked by {workspace['locked_by']} "
                    f"(expires in {(lock_time - datetime.now()).seconds // 60}m)"
                )
        
        # Update active workspace
        workspaces_data["active_workspace"] = workspace["name"]
        workspace["last_accessed"] = datetime.now().isoformat()
        workspace["last_terminal"] = self.terminal_id
        
        # Update history (most recent first)
        history = workspaces_data.get("history", [])
        if workspace["name"] in history:
            history.remove(workspace["name"])
        history.insert(0, workspace["name"])
        workspaces_data["history"] = history[:20]  # Keep last 20
        
        self.cloud.save("workspaces.json", workspaces_data)
        
        return workspace
    
    def get_active_workspace(self) -> dict:
        """Get current active workspace"""
        workspaces_data = self.cloud.get("workspaces.json")
        active_name = workspaces_data.get("active_workspace")
        
        if not active_name:
            return None
        
        for ws in workspaces_data["workspaces"]:
            if ws["name"] == active_name:
                return ws
        return None
    
    def lock_workspace(self, duration_hours: int = 2) -> None:
        """Lock workspace to current terminal"""
        workspace = self.get_active_workspace()
        if not workspace:
            raise ValueError("No active workspace")
        
        workspace["locked_by"] = self.terminal_id
        workspace["lock_expires"] = (
            datetime.now() + timedelta(hours=duration_hours)
        ).isoformat()
        
        self._save_workspace(workspace)
    
    def snapshot(self, description: str = "") -> str:
        """Create workspace snapshot"""
        workspace = self.get_active_workspace()
        if not workspace:
            raise ValueError("No active workspace")
        
        snapshot = {
            "id": f"snap_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "cwd": str(Path.cwd()),
            "git_branch": self._get_git_branch(workspace["path"]),
            "env_vars": dict(os.environ),  # Or subset
            "description": description
        }
        
        workspace.setdefault("snapshots", []).append(snapshot)
        self._save_workspace(workspace)
        
        return snapshot["id"]
    
    def export_context(self) -> dict:
        """Export workspace context as pipeable blob"""
        workspace = self.get_active_workspace()
        if not workspace:
            raise ValueError("No active workspace")
        
        return {
            "kind": "workspace_context",
            "content": {
                "name": workspace["name"],
                "path": workspace["path"],
                "git_branch": workspace.get("git_branch"),
                "env_vars": workspace.get("env_vars", {}),
                "snapshots": workspace.get("snapshots", [])
            },
            "meta": {
                "exported_by": self.terminal_id,
                "exported_at": datetime.now().isoformat()
            }
        }
    
    def _find_workspace(self, identifier: str, workspaces_data: dict) -> dict:
        """Fuzzy match workspace by name or path"""
        # Exact name match
        for ws in workspaces_data["workspaces"]:
            if ws["name"] == identifier:
                return ws
        
        # Partial name match
        matches = [
            ws for ws in workspaces_data["workspaces"]
            if identifier.lower() in ws["name"].lower()
        ]
        if len(matches) == 1:
            return matches[0]
        
        # Path match
        identifier_path = Path(identifier).resolve()
        for ws in workspaces_data["workspaces"]:
            if Path(ws["path"]).resolve() == identifier_path:
                return ws
        
        return None
```

### New Commands

```bash
# Create workspace (for bots)
@workspace create my-bot-project --python 3.11 --isolated

# Grant access to bot
@workspace grant code-bot --permissions read,write

# List workspaces
@workspace list

# Cleanup old workspaces
@workspace cleanup --older-than 7d

# Scaffold project in workspace
/projio new api.py --workspace my-bot-project --template .py#flask
```

### Integration with `/projio send`

```bash
# Send project to other bot via workspace
/projio send | /isaac workspace deliver code-bot "implement feature X"

# Code-bot receives:
# 1. Isolated workspace created
# 2. Project blob unpacked
# 3. Access token granted
# 4. Code-bot works in sandbox
# 5. Results sent back via Isaac
```

## Phase 5: Isaac-Root (Janitor) - Multi-Terminal Orchestration

### Architecture: Instances vs Root

**Isaac Instances** (per terminal):
- User-facing shell wrapper
- Execute commands, route to AI
- Sync session data to cloud
- Report heartbeat to cloud

**Isaac-Root (Janitor)**:
- Background process or cron job
- Monitors ALL Isaac instances via cloud API
- Cross-terminal coordination
- Resource cleanup and management
- System health monitoring

### Cloud Memory Structure (Shared State)

**Existing Session Files** (per user):
- `preferences.json` - User config
- `command_history.json` - Commands by terminal_id
- `aiquery_history.json` - AI queries (private)
- `task_history.json` - Tasks with status
- `learned_autofixes.json` - Corrections
- `learned_patterns.json` - Patterns

**NEW: Workspace Registry** (cloud-synced):
```json
// workspaces.json
{
  "workspaces": [
    {
      "id": "ws_abc123",
      "name": "feature-auth-system",
      "created_by": "terminal_laptop_001",
      "created_at": "2025-10-22T10:30:00Z",
      "last_accessed": "2025-10-22T14:15:00Z",
      "status": "active",  // active, idle, archived
      "path": "/home/user/Projects/isaac-ws/feature-auth-system",
      "bot_grants": [
        {
          "bot": "code-generator-v1",
          "token": "<token>",
          "expires": "2025-10-29T12:00:00Z"
        }
      ],
      "resources": {
        "disk_mb": 450,
        "file_count": 127
      }
    }
  ],
  "cleanup_rules": {
    "idle_threshold_hours": 24,
    "auto_archive_days": 7,
    "orphaned_cleanup_hours": 3
  }
}
```

**NEW: Isaac Heartbeat** (cloud-synced):
```json
// isaac_instances.json
{
  "instances": [
    {
      "terminal_id": "laptop_001",
      "hostname": "DESKTOP-NDEMI",
      "last_heartbeat": "2025-10-22T14:20:00Z",
      "status": "active",
      "current_workspace": "feature-auth-system",
      "pid": 12345
    },
    {
      "terminal_id": "server_001",
      "hostname": "PROD-WEB-01",
      "last_heartbeat": "2025-10-22T14:19:00Z",
      "status": "monitoring",
      "current_workspace": null,
      "pid": 67890
    }
  ]
}
```

### Isaac-Root Cleanup Logic

**File:** `isaac/core/janitor.py`

```python
"""
Isaac-Root (Janitor) - Multi-terminal resource management
Monitors all Isaac instances, cleans up orphaned resources
"""

from datetime import datetime, timedelta
import json
from pathlib import Path
from isaac.api.cloud_client import CloudClient

class Janitor:
    """Background cleanup and coordination for Isaac ecosystem"""
    
    def __init__(self, cloud_client: CloudClient):
        self.cloud = cloud_client
    
    def run_cleanup_cycle(self):
        """Main cleanup loop - call periodically (cron/systemd timer)"""
        
        # 1. Check instance health
        self._check_instance_health()
        
        # 2. Cleanup orphaned workspaces
        self._cleanup_orphaned_workspaces()
        
        # 3. Archive idle workspaces
        self._archive_idle_workspaces()
        
        # 4. Revoke expired bot tokens
        self._revoke_expired_tokens()
        
        # 5. Check disk usage
        self._check_disk_usage()
        
        # 6. Sync workspace registry
        self._sync_workspace_registry()
    
    def _check_instance_health(self):
        """Check if Isaac instances are still alive"""
        instances = self.cloud.get("isaac_instances.json")
        now = datetime.now()
        
        for instance in instances["instances"]:
            last_beat = datetime.fromisoformat(instance["last_heartbeat"])
            if now - last_beat > timedelta(minutes=5):
                # Instance died without cleanup
                instance["status"] = "dead"
                self._handle_dead_instance(instance)
    
    def _cleanup_orphaned_workspaces(self):
        """Clean up workspaces from dead terminals"""
        workspaces = self.cloud.get("workspaces.json")
        instances = self.cloud.get("isaac_instances.json")
        
        active_terminals = {i["terminal_id"] for i in instances["instances"] 
                           if i["status"] == "active"}
        
        for ws in workspaces["workspaces"]:
            # Workspace created by dead terminal?
            if ws["created_by"] not in active_terminals:
                # Wait grace period (3 hours default)
                created = datetime.fromisoformat(ws["created_at"])
                if datetime.now() - created > timedelta(hours=3):
                    self._archive_workspace(ws)
    
    def _archive_idle_workspaces(self):
        """Archive workspaces not accessed recently"""
        workspaces = self.cloud.get("workspaces.json")
        idle_threshold = workspaces["cleanup_rules"]["idle_threshold_hours"]
        
        for ws in workspaces["workspaces"]:
            if ws["status"] != "active":
                continue
            
            last_access = datetime.fromisoformat(ws["last_accessed"])
            if datetime.now() - last_access > timedelta(hours=idle_threshold):
                ws["status"] = "idle"
                # Archive after additional time
                if datetime.now() - last_access > timedelta(days=7):
                    self._archive_workspace(ws)
    
    def _revoke_expired_tokens(self):
        """Revoke bot access tokens that expired"""
        workspaces = self.cloud.get("workspaces.json")
        now = datetime.now()
        
        for ws in workspaces["workspaces"]:
            ws["bot_grants"] = [
                grant for grant in ws["bot_grants"]
                if datetime.fromisoformat(grant["expires"]) > now
            ]
        
        self.cloud.save("workspaces.json", workspaces)
    
    def _archive_workspace(self, workspace: dict):
        """Archive workspace to compressed storage"""
        # Create tarball of workspace
        # Move to archive directory
        # Update workspace status to "archived"
        # Free up disk space
        pass
    
    def _check_disk_usage(self):
        """Monitor disk usage across workspaces"""
        workspaces = self.cloud.get("workspaces.json")
        total_mb = sum(ws["resources"]["disk_mb"] for ws in workspaces["workspaces"])
        
        # Alert if excessive (>10GB)
        if total_mb > 10000:
            # Trigger aggressive cleanup
            pass
```

### Multi-Terminal Coordination Example

**Scenario:** User starts task on laptop, continues on desktop

```bash
# Laptop (Terminal 1) - Morning
/projio send -pro "web-dashboard" | /task "add user authentication"
# Isaac creates task_001, syncs to cloud
# Workspace created: ws_dashboard_auth

# Desktop (Terminal 2) - Afternoon (different machine!)
/task list
# Output:
# 1. [PENDING] Add user authentication to web-dashboard
#    Created: 2025-10-22 09:00 (terminal: laptop_001)
#    Workspace: ws_dashboard_auth

/task run 1
# Isaac checks cloud: workspace exists, created by laptop_001
# Laptop_001 still alive? (heartbeat check)
# Yes → Coordinate: "Workspace in use on desktop now"
# No → Take over: "Claiming orphaned workspace"

# Isaac-Root (background, every 10 minutes)
# Checks: laptop_001 last heartbeat = 8 hours ago → DEAD
# Checks: ws_dashboard_auth last access = 10 minutes ago (desktop active)
# Decision: Don't cleanup, desktop is using it
# Checks: task_001 status = IN_PROGRESS
# Decision: Let it run
```

### Server Hosting Integration (Future Phase)

**Isaac as server orchestrator:**

```bash
# Deploy app via Isaac
/isaac server deploy web-dashboard --workspace ws_dashboard_auth

# Isaac:
# 1. Validates workspace (completed, tested)
# 2. Creates deployment workspace on server
# 3. Grants deploy-bot temporary access
# 4. Monitors deployment
# 5. Registers app for health checks

# Multi-terminal monitoring
# Terminal 1 (laptop): Development
# Terminal 2 (desktop): /isaac server logs web-dashboard --follow
# Terminal 3 (mobile SSH): /isaac server status

# Isaac-Root monitors:
# - App health (HTTP checks)
# - Resource usage (CPU, memory)
# - Error rates (log analysis)
# - Auto-restart if crashed
```

**Cloud Memory enables this:**
- All terminals see deployed apps
- Health status synced across machines
- Logs accessible from any terminal
- Deployment history shared

## Phase 5: Bot Communication Protocol

### Message Format (Bot ↔ Isaac)

```json
{
  "bot": "code-generator-v1",
  "request": "workspace",
  "params": {
    "name": "feature-auth-system",
    "python": "3.11",
    "requirements": ["flask", "jwt", "sqlalchemy"],
    "project_blob": "<base64 of /projio send output>"
  },
  "credentials": {
    "isaac_token": "<bot's identity token>"
  }
}
```

**Isaac Response:**
```json
{
  "status": "created",
  "workspace": {
    "path": "/home/user/Projects/isaac-ws/feature-auth-system",
    "venv": "/home/user/Projects/isaac-ws/feature-auth-system/.venv",
    "access_token": "<workspace access token>",
    "expires": "2025-10-29T12:00:00Z"
  },
  "sandbox": {
    "allowed_commands": ["pip", "python", "git"],
    "blocked_paths": ["/etc", "/sys", "C:\\Windows"],
    "max_file_size_mb": 100
  }
}
```

## Learning Path for Implementation

### Step 1: Learn Python venv (Week 1)
- Create/activate/deactivate virtual environments
- Install packages in isolation
- Manage requirements.txt
- **Test:** `/isaac workspace create test-py --python 3.11`

### Step 2: Learn filesystem restrictions (Week 2)
- Understand OS-level protections (chroot, Docker, Windows folder permissions)
- Implement path validation (is_relative_to checks)
- Test with dangerous operations (try to write to /etc)
- **Test:** Sandbox blocks `rm -rf /etc` but allows `rm myfile.txt`

### Step 3: Learn credential management (Week 3)
- Token generation (secrets module)
- Secure storage (encrypt keystore?)
- Token validation and expiration
- **Test:** Bot requests workspace, gets token, uses token for operations

### Step 4: Build workspace scaffolding (Week 4)
- Automate venv creation
- Copy project templates
- Install dependencies from requirements.txt
- **Test:** `/projio send | /isaac workspace deliver test-bot`

### Step 5: Build bot protocol (Week 5+)
- Define JSON message format
- Implement bot registration system
- Handle workspace requests/responses
- **Test:** External bot script requests workspace, Isaac creates + grants access

## Benefits

1. **Safety First** - Joshua learned not to launch missiles; Isaac learns not to rm -rf /
2. **Bot Ecosystem** - Isaac becomes the trusted broker for all your bots
3. **Isolated Environments** - Each bot/project gets clean workspace
4. **Learning Path** - Start simple (venv), build up to full orchestration
5. **Credential Management** - Isaac holds the keys, bots request access
6. **Scalable** - Add new bots without changing Isaac core

## Success Criteria

- [ ] Sandbox mode blocks dangerous operations (system paths, huge files)
- [ ] Config console shows sandbox settings
- [ ] Can create Python/Node isolated workspaces
- [ ] Can grant/revoke bot access with tokens
- [ ] `/projio send` can deliver to bot workspaces
- [ ] Bot can work in workspace, Isaac monitors safety
- [ ] Workspace cleanup after bot finishes or timeout

---

**Priority:** MEDIUM (after Collections search fix, parallel with `/projio` port)
**Complexity:** HIGH (learning curve, security implications)
**Estimated Time:** 4-6 weeks (learning + implementation)

**Next Steps:**
1. Add sandbox settings to config console UI
2. Implement basic Sandbox class with path checking
3. Test with tier 4 commands (block if sandbox enabled)
4. Learn Python venv creation
5. Build WorkspaceManager prototype
6. Design bot communication protocol

---

**The Vision:**
Isaac becomes the **trusted orchestrator** - other bots request workspaces, Isaac creates sandboxed environments, grants credentials, monitors safety, cleans up after. You learn environment isolation by building it into Isaac, then use that knowledge to scaffold workspaces for your whole bot ecosystem.

**"Isaac has the keys" - literally.**</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_implement\sandbox_and_workspace_system.md