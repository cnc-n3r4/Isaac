# Implementation: Main Entry Point

## Goal
Create __main__.py to wire all components together and handle CLI arguments.

**Time Estimate:** 30 minutes

**Dependencies:** ALL previous implementation files (this is the final wiring)

---

## File: __main__.py

**Path:** `isaac/__main__.py`

**Purpose:** Entry point for `isaac` command, handles CLI args and startup sequence.

**Complete Implementation:**

```python
"""
Isaac 2.0 - Main Entry Point
Multi-platform intelligent shell assistant with cloud sync.
"""

import sys
import argparse
import socket
from pathlib import Path
from isaac.ui.splash_screen import show_splash
from isaac.ui.header_display import HeaderDisplay
from isaac.ui.prompt_handler import PromptHandler
from isaac.adapters.shell_detector import detect_shell
from isaac.core.session_manager import SessionManager


def load_user_config():
    """
    Load user configuration from ~/.isaac/config.json.
    Creates default if missing.
    
    Returns:
        dict: Configuration dictionary
    """
    import json
    
    config_dir = Path.home() / '.isaac'
    config_file = config_dir / 'config.json'
    
    # Default config
    default_config = {
        'machine_id': socket.gethostname(),
        'api_url': '',
        'api_key': ''
    }
    
    try:
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
        
        if not config_file.exists():
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Isaac > Created default config at {config_file}")
        
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Isaac > Error loading config: {str(e)}")
        return default_config


def launch_shell():
    """
    Main startup sequence for `isaac --start`.
    
    Process:
    1. Load config
    2. Show splash screen
    3. Detect shell (PowerShell/bash)
    4. Load session from local storage
    5. Render header
    6. Start interactive loop
    """
    # Load config
    config = load_user_config()
    
    # Show splash (5.5 seconds, non-skippable)
    show_splash()
    
    # Detect shell
    try:
        shell_adapter = detect_shell()
    except RuntimeError as e:
        print(str(e))
        sys.exit(1)
    
    # Load session
    session_mgr = SessionManager(config, shell_adapter)
    session_mgr.load_from_local()
    
    # Initialize UI
    header = HeaderDisplay(session_mgr, shell_adapter)
    header.render_locked_header()
    
    # Start interactive loop
    prompt = PromptHandler(session_mgr, shell_adapter, header)
    prompt.run_interactive_loop()


def show_command_history(all_machines=False):
    """
    Display command history.
    
    Args:
        all_machines: If True, show all machines; else current only
    """
    config = load_user_config()
    shell_adapter = detect_shell()
    session = SessionManager(config, shell_adapter)
    session.load_from_local()
    
    if all_machines:
        entries = session.command_history.entries
        print(f"Isaac > Command history (all machines):\n")
    else:
        entries = session.command_history.get_by_machine(session.machine_id)
        print(f"Isaac > Command history ({session.machine_id}):\n")
    
    if not entries:
        print("  No commands in history.")
        return
    
    for entry in entries[-20:]:  # Last 20
        timestamp = entry.timestamp[:19]  # Trim milliseconds
        print(f"  [{entry.machine}] {timestamp} | {entry.command}")


def list_machines():
    """List all machines that have command history."""
    config = load_user_config()
    shell_adapter = detect_shell()
    session = SessionManager(config, shell_adapter)
    session.load_from_local()
    
    machines = set(e.machine for e in session.command_history.entries)
    
    print(f"Isaac > Active machines ({len(machines)}):\n")
    if machines:
        for machine in sorted(machines):
            count = len(session.command_history.get_by_machine(machine))
            print(f"  {machine} ({count} commands)")
    else:
        print("  No machines found.")


def show_help():
    """Display help text from data/help_text.txt or inline fallback."""
    help_file = Path(__file__).parent / 'data' / 'help_text.txt'
    
    if help_file.exists():
        print(help_file.read_text())
    else:
        # Inline fallback
        print("""
Isaac 2.0 - Multi-Platform Shell Assistant

USAGE:
  isaac --start              Launch Isaac shell
  isaac --help               Show this help
  isaac --show-log           Show command history (current machine)
  isaac --show-log --all     Show command history (all machines)
  isaac --machines           List all active machines

INTERACTIVE COMMANDS:
  exit                       Quit Isaac
  quit                       Quit Isaac

COMMAND TIERS:
  Tier 1:   Instant (ls, cd, pwd)
  Tier 3:   Confirm (git, cp, mv)
  Tier 4:   Lockdown (rm -rf, format)

CONFIG:
  ~/.isaac/config.json       User configuration
  
MORE INFO:
  Documentation: https://github.com/yourusername/isaac
""")


def main():
    """
    Main entry point for Isaac CLI.
    Parses arguments and routes to appropriate handler.
    """
    parser = argparse.ArgumentParser(
        prog='isaac',
        description='Isaac 2.0 - Multi-platform intelligent shell assistant'
    )
    
    parser.add_argument(
        '--start',
        action='store_true',
        help='Launch Isaac interactive shell'
    )
    
    parser.add_argument(
        '--show-log',
        action='store_true',
        help='Show command history'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show history from all machines (use with --show-log)'
    )
    
    parser.add_argument(
        '--machines',
        action='store_true',
        help='List all active machines'
    )
    
    parser.add_argument(
        '--help-full',
        action='store_true',
        help='Show full help documentation'
    )
    
    args = parser.parse_args()
    
    # Route to appropriate handler
    if args.start:
        launch_shell()
    
    elif args.show_log:
        show_command_history(all_machines=args.all)
    
    elif args.machines:
        list_machines()
    
    elif args.help_full:
        show_help()
    
    else:
        # No args - show basic help
        parser.print_help()


if __name__ == '__main__':
    main()
```

---

## Verification Steps

### 1. Test Config Loading
```python
from isaac.__main__ import load_user_config

config = load_user_config()
print(f"Config keys: {list(config.keys())}")
print(f"Machine ID: {config.get('machine_id')}")

# Should create ~/.isaac/config.json on first run
# Expected output:
# Config keys: ['machine_id', 'api_url', 'api_key']
# Machine ID: YOUR-HOSTNAME
```

### 2. Test Command Line Arguments
```bash
# Test help
isaac --help

# Expected: argparse help output

# Test full help
isaac --help-full

# Expected: Full help text from help_text.txt
```

### 3. Test Show Log (After Running Isaac)
```bash
# First, run isaac and execute a few commands
isaac --start
# user> ls
# user> echo test
# user> exit

# Then check log
isaac --show-log

# Expected: List of commands with timestamps and machine name
```

### 4. Test Full Launch
```bash
isaac --start
```

**Expected Sequence:**
1. Splash displays (5.5s)
2. Screen clears
3. Header appears (3 lines + separator)
4. Prompt shows: `isaac> Ready.`
5. Can type commands
6. Commands execute
7. Output appears below header
8. Header never scrolls
9. `exit` quits cleanly

### 5. Test Multi-Machine (Simulated)
```python
# Manually edit ~/.isaac/command_history.json
# Add entries with different machine_id values
# Then run:

isaac --machines

# Expected: List of all machines with command counts

isaac --show-log --all

# Expected: Commands from all machines
```

---

## Common Pitfalls

⚠️ **Module not found errors**
- **Symptom:** `ModuleNotFoundError: No module named 'isaac.ui'`
- **Fix:** Ensure all `__init__.py` files exist, run `pip install -e .`

⚠️ **Config file permission denied**
- **Symptom:** `PermissionError` creating ~/.isaac/config.json
- **Fix:** Check write permissions on home directory

⚠️ **Shell detection fails**
- **Symptom:** `RuntimeError: No compatible shell found`
- **Fix:** Install PowerShell (Windows) or bash (Linux)

⚠️ **Splash doesn't show**
- **Symptom:** Goes straight to prompt
- **Fix:** Verify splash_screen.py is being called in launch_shell()

⚠️ **Commands don't execute**
- **Symptom:** Prompt appears but commands do nothing
- **Fix:** Check CommandRouter is wired correctly in PromptHandler

---

## Integration Test (End-to-End)

**Full System Test:**

```bash
# 1. Install Isaac
cd /path/to/isaac
pip install -e .

# 2. Launch
isaac --start

# Expected: Splash → Header → Prompt

# 3. Test Tier 1 (instant)
user> ls
# [directory listing appears]

# 4. Test Tier 3 (confirm)
user> git status
# Isaac > Validate this command: git status? [y/N]: y
# [git output appears]

# 5. Test Tier 4 (lockdown)
user> rm -rf test
# [Lockdown warning appears]
# Isaac > Proceed? no
# Aborted.

# 6. Check history
user> exit
isaac --show-log
# [Commands listed with timestamps]

# 7. Test help
isaac --help-full
# [Full help text displays]
```

**If all steps work:** ✅ Main entry point complete!

---

## Success Signals

✅ Config loads from ~/.isaac/config.json  
✅ Default config created on first run  
✅ `isaac --start` launches splash + shell  
✅ `isaac --show-log` displays history  
✅ `isaac --show-log --all` shows all machines  
✅ `isaac --machines` lists machines  
✅ `isaac --help` shows argparse help  
✅ `isaac --help-full` shows full docs  
✅ All components wire together correctly  
✅ Ready for next step (PHP API)

---

**Next Step:** 09_impl_php_api.md (Create GoDaddy cloud sync endpoints)

---

**END OF MAIN ENTRY POINT IMPLEMENTATION**
