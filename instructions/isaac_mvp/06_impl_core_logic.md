# Implementation: Core Logic (Part 1 - TierValidator + CommandRouter)

## Goal
Create tier_validator.py and command_router.py - the heart of Isaac's command routing system.

**Time Estimate:** 45 minutes total (Part 1: 30 min, Part 2: 15 min)

**Dependencies:** 
- 03_impl_data_files.md (tier_defaults.json must exist)
- 04_impl_shell_adapters.md (shell adapters)
- 05_impl_models.md (Preferences model)

---

## File 1: tier_validator.py

**Path:** `isaac/core/tier_validator.py`

**Purpose:** Classify commands into tiers (1, 2, 2.5, 3, 4) for safety validation.

**Complete Implementation:**

```python
"""
Tier validator for command classification.
Maps commands to safety tiers for execution control.
"""

import json
from pathlib import Path
from typing import Dict, List


class TierValidator:
    """Validate and classify commands into safety tiers."""
    
    def __init__(self, preferences=None):
        """
        Initialize tier validator.
        
        Args:
            preferences: Preferences instance with tier_overrides
        """
        self.preferences = preferences
        self.defaults = self._load_tier_defaults()
        self.custom_overrides = preferences.tier_overrides if preferences else {}
    
    def get_tier(self, command: str) -> int:
        """
        Get tier for command.
        
        Args:
            command: Full command string
            
        Returns:
            int: Tier (1, 2, 2.5, 3, or 4)
                 Defaults to 3 (safe) for unknown commands
        """
        # Extract command name (first word)
        parts = command.strip().split()
        if not parts:
            return 3  # Empty command, default to Tier 3
        
        cmd_name = parts[0]
        
        # Check custom overrides first
        if cmd_name in self.custom_overrides:
            return self.custom_overrides[cmd_name]
        
        # Check defaults
        for tier, commands in self.defaults.items():
            if cmd_name in commands:
                # Convert tier key to int/float
                tier_num = float(tier) if '.' in tier else int(tier)
                return tier_num
        
        # Unknown command defaults to Tier 3 (requires validation)
        return 3
    
    def _load_tier_defaults(self) -> Dict[str, List[str]]:
        """
        Load tier_defaults.json from data directory.
        
        Returns:
            Dict mapping tier (as string) to list of commands
        """
        # Get path to data directory
        data_dir = Path(__file__).parent.parent / 'data'
        tier_file = data_dir / 'tier_defaults.json'
        
        if not tier_file.exists():
            # Fallback to minimal defaults if file missing
            return {
                '1': ['ls', 'cd', 'pwd'],
                '4': ['rm', 'del', 'format']
            }
        
        with open(tier_file, 'r') as f:
            return json.load(f)
```

---

## File 2: command_router.py

**Path:** `isaac/core/command_router.py`

**Purpose:** Route commands through tier system and execute or prompt for confirmation.

**Complete Implementation:**

```python
"""
Command router for tier-based execution control.
Routes commands to appropriate handling based on tier classification.
"""

from isaac.core.tier_validator import TierValidator
from isaac.adapters.base_adapter import CommandResult


class CommandRouter:
    """Route commands through tier system for execution."""
    
    def __init__(self, session_mgr, shell_adapter):
        """
        Initialize command router.
        
        Args:
            session_mgr: SessionManager instance
            shell_adapter: Shell adapter (PowerShell/bash)
        """
        self.session = session_mgr
        self.shell = shell_adapter
        self.tier_validator = TierValidator(session_mgr.preferences)
    
    def route_command(self, input_text: str) -> CommandResult:
        """
        Main routing logic for command execution.
        
        Process:
        1. Check if natural language (requires 'isaac' prefix for MVP)
        2. Determine tier
        3. Execute or validate based on tier
        
        Args:
            input_text: User input (command or natural language)
            
        Returns:
            CommandResult with execution status and output
        """
        input_text = input_text.strip()
        
        # Check for empty input
        if not input_text:
            return CommandResult(
                success=False,
                output='',
                exit_code=0
            )
        
        # Natural language check (MVP: reject without 'isaac' prefix)
        if self._is_natural_language(input_text):
            if not input_text.lower().startswith('isaac '):
                return CommandResult(
                    success=False,
                    output="Isaac > I have a name, use it.",
                    exit_code=-1
                )
            # AI integration in Phase 2
            return CommandResult(
                success=False,
                output="Isaac > AI integration coming in Phase 2.",
                exit_code=-1
            )
        
        # Shell command - determine tier
        tier = self.tier_validator.get_tier(input_text)
        
        # Tier 1: Instant execution
        if tier == 1:
            return self.shell.execute(input_text)
        
        # Tier 2: Auto-correct typos (MVP: just execute, AI in Phase 2)
        elif tier == 2:
            # Future: AI auto-correction
            # For MVP: just execute
            return self.shell.execute(input_text)
        
        # Tier 2.5: Correct + confirm (MVP: just confirm, AI in Phase 2)
        elif tier == 2.5:
            # Future: AI correction, then confirm
            # For MVP: just confirm
            confirmed = self._confirm(f"Execute: {input_text}?")
            if confirmed:
                return self.shell.execute(input_text)
            else:
                return CommandResult(
                    success=False,
                    output="Isaac > Aborted.",
                    exit_code=-1
                )
        
        # Tier 3: Validation required (MVP: simple confirm, AI in Phase 2)
        elif tier == 3:
            # Future: AI validation
            # For MVP: simple confirmation
            confirmed = self._confirm(f"Validate this command: {input_text}?")
            if confirmed:
                return self.shell.execute(input_text)
            else:
                return CommandResult(
                    success=False,
                    output="Isaac > Aborted.",
                    exit_code=-1
                )
        
        # Tier 4: Lockdown warnings
        elif tier == 4:
            return self._handle_tier4(input_text)
        
        else:
            # Unknown tier, default to Tier 3 behavior
            confirmed = self._confirm(f"Execute: {input_text}?")
            if confirmed:
                return self.shell.execute(input_text)
            else:
                return CommandResult(
                    success=False,
                    output="Isaac > Aborted.",
                    exit_code=-1
                )
    
    def _is_natural_language(self, text: str) -> bool:
        """
        Heuristic to detect natural language vs shell command.
        
        Simple check: if text contains question words or lacks shell keywords,
        it's probably natural language.
        
        Args:
            text: Input text
            
        Returns:
            bool: True if likely natural language
        """
        text_lower = text.lower()
        
        # Check for question words
        question_words = ['what', 'when', 'where', 'who', 'why', 'how']
        if any(word in text_lower.split() for word in question_words):
            return True
        
        # Check for common shell keywords (if present, probably a command)
        shell_keywords = ['ls', 'cd', 'git', 'grep', 'find', '|', '>', '<', '&&', 'sudo']
        has_shell_keywords = any(kw in text.split() for kw in shell_keywords)
        
        # If has spaces but no shell keywords, likely natural language
        return ' ' in text and not has_shell_keywords
    
    def _confirm(self, prompt: str) -> bool:
        """
        Prompt user for confirmation.
        
        Args:
            prompt: Confirmation message
            
        Returns:
            bool: True if user confirms, False otherwise
        """
        response = input(f"Isaac > {prompt} [y/N]: ").strip().lower()
        return response in ['y', 'yes']
    
    def _handle_tier4(self, command: str) -> CommandResult:
        """
        Handle Tier 4 (destructive) commands with lockdown warnings.
        
        Requires exact 'yes' (not just 'y') to proceed.
        
        Args:
            command: Tier 4 command to execute
            
        Returns:
            CommandResult
        """
        print("\n" + "=" * 60)
        print("⚠️  DESTRUCTIVE COMMAND WARNING ⚠️")
        print("=" * 60)
        print(f"Command: {command}")
        print("\nThis command can cause data loss or system damage.")
        print("Type 'yes' (exactly) to proceed, or anything else to abort.")
        print("=" * 60)
        
        response = input("Isaac > Proceed? ").strip()
        
        if response == 'yes':
            return self.shell.execute(command)
        else:
            return CommandResult(
                success=False,
                output="Isaac > Aborted. (Type 'yes' exactly to execute Tier 4 commands)",
                exit_code=-1
            )
```

---

## Verification Steps

### 1. Test TierValidator
```python
from isaac.core.tier_validator import TierValidator
from isaac.models.preferences import Preferences

# Test with default preferences
prefs = Preferences()
validator = TierValidator(prefs)

# Test Tier 1 commands
assert validator.get_tier('ls') == 1
assert validator.get_tier('cd /tmp') == 1
assert validator.get_tier('pwd') == 1
print("✅ Tier 1 commands classified")

# Test Tier 3 commands
assert validator.get_tier('git status') == 3
assert validator.get_tier('cp file1 file2') == 3
print("✅ Tier 3 commands classified")

# Test Tier 4 commands
assert validator.get_tier('rm -rf /') == 4
assert validator.get_tier('format C:') == 4
print("✅ Tier 4 commands classified")

# Test unknown command (defaults to 3)
assert validator.get_tier('unknown_command') == 3
print("✅ Unknown commands default to Tier 3")

# Test custom overrides
prefs.tier_overrides = {'find': 1}
validator = TierValidator(prefs)
assert validator.get_tier('find /') == 1
print("✅ Custom tier overrides work")
```

### 2. Test CommandRouter (Basic Routing)
```python
from isaac.core.command_router import CommandRouter
from isaac.adapters.shell_detector import detect_shell
from isaac.core.session_manager import SessionManager  # Assuming this exists
from isaac.utils.config_loader import load_user_config  # Assuming this exists

# Initialize dependencies
config = load_user_config()
shell = detect_shell()
session = SessionManager(config, shell)
router = CommandRouter(session, shell)

# Test Tier 1 (instant execution)
result = router.route_command('echo test')
print(f"Tier 1 result: {result.output.strip()}")
print(f"Success: {result.success}")
```

### 3. Test Natural Language Detection
```python
from isaac.core.command_router import CommandRouter

# Create minimal router for testing
class MockSession:
    def __init__(self):
        from isaac.models.preferences import Preferences
        self.preferences = Preferences()

class MockShell:
    def execute(self, cmd):
        from isaac.adapters.base_adapter import CommandResult
        return CommandResult(True, 'mock output', 0)

session = MockSession()
shell = MockShell()
router = CommandRouter(session, shell)

# Test natural language detection
assert router._is_natural_language('what time is it') == True
assert router._is_natural_language('ls -la') == False
assert router._is_natural_language('git status') == False
assert router._is_natural_language('how do I list files') == True
print("✅ Natural language detection works")
```

---

## Common Pitfalls

⚠️ **tier_defaults.json not found**
- **Symptom:** `FileNotFoundError` or fallback defaults used
- **Fix:** Ensure file exists in `isaac/data/tier_defaults.json`

⚠️ **Tier classification wrong**
- **Symptom:** Commands execute when they should prompt
- **Fix:** Check tier_defaults.json has correct command mappings

⚠️ **Natural language check too strict**
- **Symptom:** Valid commands rejected as natural language
- **Fix:** Adjust `_is_natural_language()` heuristic

⚠️ **Confirmation hangs in tests**
- **Symptom:** Tests wait for input()
- **Fix:** Mock `input()` in tests or skip interactive tests

---

## Success Signals

✅ TierValidator loads tier_defaults.json  
✅ get_tier() returns correct tier for known commands  
✅ Unknown commands default to Tier 3  
✅ Custom tier overrides work  
✅ CommandRouter instantiates without errors  
✅ Tier 1 commands execute immediately  
✅ Tier 3/4 commands prompt for confirmation  
✅ Natural language detection works  
✅ Ready for Part 2 (SessionManager)

---

**Next:** 06_impl_core_logic_part2.md (SessionManager for cloud sync)

---

**END OF CORE LOGIC PART 1**
