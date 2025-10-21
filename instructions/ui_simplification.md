# ISAAC UI Simplification - Implementation Instructions

## Overview
Remove complex terminal control system and replace with simple text-based output flow. The current locked-header approach is causing output stacking issues on Windows. We're moving to a traditional shell model where commands and output stack naturally.

## Goal
Transform ISAAC from complex terminal UI → simple prompt/output loop with meta-commands for configuration.

---

## Phase 1: Remove Terminal Control Complexity

### 1.1 Backup Current State
```powershell
git checkout -b ui-simplification
git add -A
git commit -m "Backup before UI simplification"
```

### 1.2 Modify `isaac/ui/permanent_shell.py`

**Current structure to replace:**
- Complex screen management with `TerminalControl`
- Status threads and dirty flags
- Scroll region handling
- Config mode special UI

**New simplified structure:**

```python
# isaac/ui/permanent_shell.py

import sys
from isaac.core.command_router import CommandRouter
from isaac.core.session_manager import SessionManager
from isaac.adapters.powershell_adapter import PowerShellAdapter
from isaac.adapters.bash_adapter import BashAdapter

class PermanentShell:
    def __init__(self):
        self.session = SessionManager()
        self.shell = self._detect_shell()
        self.router = CommandRouter(self.shell, self.session)
        
    def _detect_shell(self):
        """Detect and return appropriate shell adapter"""
        if sys.platform == 'win32':
            return PowerShellAdapter()
        else:
            return BashAdapter()
    
    def _print_welcome(self):
        """Print startup banner with key info"""
        version = "1.0.2"  # Get from config
        session_id = self.session.session_id[:6]
        
        cloud_status = "✓" if self.session.cloud_enabled else "✗"
        ai_status = "✓" if self.session.ai_enabled else "✗"
        
        print("=" * 60)
        print(f"ISAAC v{version}")
        print(f"Session: {session_id} | Cloud: {cloud_status} | AI: {ai_status}")
        print("Type /help for available commands")
        print("=" * 60)
        print()
    
    def run(self):
        """Main shell loop - simplified"""
        self._print_welcome()
        
        while True:
            try:
                # Print prompt
                print("> ", end='', flush=True)
                
                # Get user input
                user_input = input().strip()
                
                # Skip empty input
                if not user_input:
                    continue
                
                # Handle exit
                if user_input.lower() in ['exit', 'quit', '/exit', '/quit']:
                    print("Goodbye!")
                    break
                
                # Route command through existing system
                result = self.router.route_command(user_input)
                
                # Print output
                if result.output:
                    print(result.output)
                
                # Print any errors
                if not result.success and result.exit_code != 0:
                    print(f"Error (exit code {result.exit_code})", file=sys.stderr)
                    
            except KeyboardInterrupt:
                print("\nUse 'exit' or '/exit' to quit")
                continue
            except EOFError:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Unexpected error: {e}", file=sys.stderr)
                continue

def main():
    """Entry point for isaac command"""
    shell = PermanentShell()
    shell.run()

if __name__ == '__main__':
    main()
```

### 1.3 Remove or Archive `isaac/ui/terminal_control.py`

**Action:** Move to archive folder (don't delete yet, in case we need reference)

```powershell
New-Item -ItemType Directory -Force -Path "isaac/ui/_archived"
Move-Item "isaac/ui/terminal_control.py" "isaac/ui/_archived/"
```

### 1.4 Simplify `isaac/ui/advanced_input.py`

**Current:** Complex keyboard handling for config mode
**New:** Either remove entirely (use built-in `input()`) or keep minimal readline support

**Recommendation:** Remove for now. Add back later if needed for history navigation.

```powershell
Move-Item "isaac/ui/advanced_input.py" "isaac/ui/_archived/"
```

---

## Phase 2: Expand Meta-Command System

### 2.1 Create Enhanced `/config` Command

**File:** `isaac/commands/config.py`

```python
# isaac/commands/config.py

from isaac.core.session_manager import SessionManager
from isaac.api.cloud_client import CloudClient
from isaac.ai.xai_client import XaiClient

class ConfigCommand:
    def __init__(self, session: SessionManager):
        self.session = session
    
    def execute(self, args: list) -> str:
        """
        Handle /config commands
        
        Usage:
            /config              - Show overview
            /config status       - Detailed status
            /config ai           - AI provider details
            /config cloud        - Cloud sync details
            /config plugins      - List plugins
            /config set <k> <v>  - Set configuration value
        """
        if not args:
            return self._show_overview()
        
        subcommand = args[0].lower()
        
        if subcommand == 'status':
            return self._show_status()
        elif subcommand == 'ai':
            return self._show_ai_details()
        elif subcommand == 'cloud':
            return self._show_cloud_details()
        elif subcommand == 'plugins':
            return self._show_plugins()
        elif subcommand == 'set':
            if len(args) < 3:
                return "Usage: /config set <key> <value>"
            return self._set_config(args[1], args[2])
        else:
            return f"Unknown subcommand: {subcommand}\nUse /config for help"
    
    def _show_overview(self) -> str:
        """Show configuration overview"""
        lines = []
        lines.append("=== ISAAC Configuration ===")
        lines.append(f"Version: {self._get_version()}")
        lines.append(f"Session ID: {self.session.session_id}")
        lines.append(f"History Count: {len(self.session.command_history)}")
        lines.append(f"Default Tier: {self.session.preferences.get('default_tier', 2)}")
        lines.append("")
        lines.append("Available subcommands:")
        lines.append("  /config status   - System status check")
        lines.append("  /config ai       - AI provider details")
        lines.append("  /config cloud    - Cloud sync status")
        lines.append("  /config plugins  - Available plugins")
        lines.append("  /config set <key> <value> - Change setting")
        return "\n".join(lines)
    
    def _show_status(self) -> str:
        """Show detailed system status"""
        lines = []
        lines.append("=== System Status ===")
        
        # Cloud status
        cloud_status = self._check_cloud_status()
        lines.append(f"Cloud: {cloud_status}")
        
        # AI status
        ai_status = self._check_ai_status()
        lines.append(f"AI Provider: {ai_status}")
        
        # Network info
        import socket
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
            lines.append(f"Network: {ip}")
        except:
            lines.append("Network: Unable to detect")
        
        # Session info
        lines.append(f"Session: {self.session.session_id}")
        lines.append(f"Commands today: {len(self.session.command_history)}")
        
        return "\n".join(lines)
    
    def _show_ai_details(self) -> str:
        """Show AI provider configuration"""
        lines = []
        lines.append("=== AI Provider Details ===")
        
        provider = self.session.preferences.get('ai_provider', 'xai')
        model = self.session.preferences.get('ai_model', 'grok-beta')
        
        lines.append(f"Provider: {provider}")
        lines.append(f"Model: {model}")
        
        # Try to ping the API
        try:
            # This is pseudocode - adapt to your actual client
            client = XaiClient(
                api_key=self.session.preferences.get('xai_api_key'),
                api_url=self.session.preferences.get('xai_api_url'),
                model=model
            )
            # Add a simple health check method to your client
            status = "✓ Connected"
        except Exception as e:
            status = f"✗ Error: {str(e)}"
        
        lines.append(f"Status: {status}")
        
        return "\n".join(lines)
    
    def _show_cloud_details(self) -> str:
        """Show cloud sync status"""
        lines = []
        lines.append("=== Cloud Sync Status ===")
        
        if not self.session.cloud_enabled:
            lines.append("Cloud sync: Disabled")
            lines.append("Enable in config: /config set cloud_enabled true")
            return "\n".join(lines)
        
        lines.append("Cloud sync: Enabled")
        
        try:
            # Check cloud client status
            client = CloudClient(
                api_url=self.session.preferences.get('cloud_api_url'),
                bearer_token=self.session.preferences.get('cloud_bearer_token')
            )
            
            # Pseudocode - add health check to your CloudClient
            health = client.health_check()
            if health.get('status') == 'ok':
                lines.append("Connection: ✓ Healthy")
                lines.append(f"Last sync: {health.get('last_sync', 'Unknown')}")
            else:
                lines.append("Connection: ✗ Unhealthy")
        except Exception as e:
            lines.append(f"Connection: ✗ Error - {str(e)}")
        
        return "\n".join(lines)
    
    def _show_plugins(self) -> str:
        """List available plugins"""
        lines = []
        lines.append("=== Available Plugins ===")
        
        # For now, hardcode known plugins
        # Later, scan isaac/commands/ directory
        plugins = [
            ("togrok", "Vector search collections", True),
            ("backup", "Config backup/restore", True),
            ("task_planner", "Multi-step task execution", True),
        ]
        
        for name, desc, enabled in plugins:
            status = "✓" if enabled else "✗"
            lines.append(f"{status} {name:15} - {desc}")
        
        return "\n".join(lines)
    
    def _set_config(self, key: str, value: str) -> str:
        """Set a configuration value"""
        # Define allowed config keys
        allowed_keys = {
            'default_tier': int,
            'cloud_enabled': lambda v: v.lower() in ['true', '1', 'yes'],
            'ai_provider': str,
            'ai_model': str,
        }
        
        if key not in allowed_keys:
            return f"Unknown config key: {key}\nAllowed: {', '.join(allowed_keys.keys())}"
        
        try:
            # Convert value to correct type
            converter = allowed_keys[key]
            converted_value = converter(value)
            
            # Update preferences
            self.session.preferences[key] = converted_value
            self.session.save_preferences()
            
            return f"✓ Set {key} = {converted_value}"
        except Exception as e:
            return f"✗ Error setting {key}: {str(e)}"
    
    def _get_version(self) -> str:
        """Get ISAAC version"""
        # Read from setup.py or version file
        return "1.0.2"  # Hardcoded for now
    
    def _check_cloud_status(self) -> str:
        """Quick cloud status check"""
        if not self.session.cloud_enabled:
            return "✗ Disabled"
        
        try:
            # Quick health check
            return "✓ Connected"
        except:
            return "✗ Unreachable"
    
    def _check_ai_status(self) -> str:
        """Quick AI status check"""
        provider = self.session.preferences.get('ai_provider', 'xai')
        model = self.session.preferences.get('ai_model', 'grok-beta')
        
        try:
            # Quick ping
            return f"✓ {provider} ({model})"
        except:
            return f"✗ {provider} unreachable"
```

### 2.2 Create `/status` Quick Command

**File:** `isaac/commands/status.py`

```python
# isaac/commands/status.py

from isaac.core.session_manager import SessionManager

class StatusCommand:
    def __init__(self, session: SessionManager):
        self.session = session
    
    def execute(self, args: list) -> str:
        """
        Quick status check
        
        Usage:
            /status       - One-line summary
            /status -v    - Verbose (same as /config status)
        """
        if args and args[0] == '-v':
            # Delegate to config command
            from isaac.commands.config import ConfigCommand
            return ConfigCommand(self.session)._show_status()
        
        # One-line summary
        cloud = "✓" if self.session.cloud_enabled else "✗"
        ai = "✓" if self.session.preferences.get('ai_provider') else "✗"
        hist = len(self.session.command_history)
        
        return f"Session: {self.session.session_id[:6]} | Cloud: {cloud} | AI: {ai} | History: {hist}"
```

### 2.3 Update Command Router

**File:** `isaac/core/command_router.py`

**Modify the `route_command` method to handle new meta-commands:**

```python
# In isaac/core/command_router.py

def route_command(self, user_input: str):
    """Route command based on prefix and type"""
    
    # Check for meta-commands first
    if user_input.startswith('/'):
        return self._handle_meta_command(user_input)
    
    # ... rest of existing routing logic ...

def _handle_meta_command(self, command: str):
    """Handle /commands"""
    parts = command[1:].split()  # Remove leading / and split
    cmd_name = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    # Import commands
    from isaac.commands.config import ConfigCommand
    from isaac.commands.status import StatusCommand
    from isaac.commands.help import HelpCommand
    
    # Route to appropriate handler
    if cmd_name == 'config':
        handler = ConfigCommand(self.session)
        output = handler.execute(args)
    elif cmd_name == 'status':
        handler = StatusCommand(self.session)
        output = handler.execute(args)
    elif cmd_name == 'help':
        handler = HelpCommand(self.session)
        output = handler.execute(args)
    elif cmd_name in ['exit', 'quit']:
        # This will be handled in main loop
        return CommandResult(success=True, output="", exit_code=0)
    elif cmd_name == 'clear':
        # Clear screen
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        return CommandResult(success=True, output="", exit_code=0)
    else:
        output = f"Unknown command: /{cmd_name}\nType /help for available commands"
    
    return CommandResult(
        success=True,
        output=output,
        exit_code=0
    )
```

---

## Phase 3: Update Entry Point

### 3.1 Verify `isaac/__main__.py`

Make sure it calls the simplified shell:

```python
# isaac/__main__.py

from isaac.ui.permanent_shell import main

if __name__ == '__main__':
    main()
```

### 3.2 Test Entry Point

```powershell
# Reinstall in development mode
pip install -e .

# Test the command
isaac
```

---

## Phase 4: Testing Checklist

### 4.1 Basic Functionality
- [ ] `isaac` command launches shell
- [ ] Simple commands execute (ls, pwd, cd)
- [ ] Output prints correctly without stacking issues
- [ ] Prompt appears after each command
- [ ] Exit command works

### 4.2 Meta-Commands
- [ ] `/help` shows available commands
- [ ] `/status` shows one-line summary
- [ ] `/config` shows overview
- [ ] `/config status` shows detailed status
- [ ] `/config ai` shows AI provider info
- [ ] `/config cloud` shows cloud sync info
- [ ] `/config plugins` lists plugins
- [ ] `/config set <key> <value>` changes settings
- [ ] `/clear` clears screen

### 4.3 AI Features
- [ ] `isaac <query>` translates to shell command
- [ ] AI responses print correctly
- [ ] Tier validation still works for dangerous commands
- [ ] AI validation prompts for confirmation when needed

### 4.4 Cloud Sync
- [ ] Cloud sync still works (if enabled)
- [ ] Command history persists
- [ ] Preferences save correctly

---

## Phase 5: Cleanup

### 5.1 Remove Dead Code

After testing confirms everything works:

```powershell
# Remove archived files
Remove-Item -Recurse "isaac/ui/_archived"

# Remove any unused imports
# (Manual review of files)
```

### 5.2 Update Documentation

- [ ] Update README.md with new UI approach
- [ ] Update copilot-instructions.md to reflect simplified architecture
- [ ] Remove references to TerminalControl from docs

### 5.3 Commit Changes

```powershell
git add -A
git commit -m "Simplify UI: Remove complex terminal control, add meta-commands"
git push origin ui-simplification
```

---

## Expected Outcome

**Before:**
- Complex terminal management with locked headers
- Output stacking issues
- Platform-specific rendering problems
- Hard to debug screen updates

**After:**
- Simple prompt → output → prompt flow
- Natural text stacking (like any normal shell)
- Works consistently across terminals
- Easy to maintain and debug
- Configuration via explicit `/config` commands

---

## Rollback Plan

If something breaks:

```powershell
git checkout isaac-win  # Return to previous branch
git branch -D ui-simplification  # Delete failed attempt
```

The archived files in `isaac/ui/_archived/` can be restored if needed.

---

## Notes

1. **Keep existing core logic intact** - CommandRouter, TierValidator, SessionManager, AI components should not change
2. **Only UI layer changes** - Everything in `isaac/ui/` is being simplified
3. **Meta-commands are extensible** - Easy to add more `/commands` later
4. **Testing is critical** - Make sure AI validation and tier system still work correctly

---

## Questions/Issues

If you encounter problems:

1. Check that `CommandRouter.route_command()` still returns `CommandResult` objects
2. Verify `SessionManager` methods haven't changed signatures
3. Test with both PowerShell and Windows Terminal
4. Check that cloud sync still works if enabled
