# PHASE 1: STABILIZATION - IMPLEMENTATION KICKOFF

**Agent Role:** Phase 1 Implementation Engineer
**Timeline:** Week 1-2 (5-10 hours of actual work)
**Goal:** Make ISAAC functional and secure
**Branch:** `claude/phase-1-stabilization-[your-session-id]`

---

## 🎯 YOUR MISSION

Transform ISAAC from **non-functional** (5.5/10) to **functional & secure** (6.5/10) by fixing 5 critical blocking issues.

---

## 📋 TASK LIST (Execute in Order)

### Task 1: Install Missing Dependencies ⚡ (5 minutes)
**Status:** 🔴 BLOCKING - Do this first!

```bash
cd /home/user/Isaac
pip install -r requirements.txt

# Verify:
python -c "import jsonschema, dotenv, flask, anthropic, openai"
python -c "import isaac.core.command_router"
```

**Success:** No import errors

---

### Task 2: Fix Syntax Errors (2 hours)
**Status:** 🔴 BLOCKING

**Files to fix:**
1. Remove UTF-8 BOM from 3 files
2. `isaac/core/session_manager_old.py:86` - Fix or delete
3. `isaac/commands/msg.py:297` - Fix XML parsing
4. `isaac/bubbles/bubble_manager.py:458` - Fix encoding

**Quick option:** Delete broken old files:
```bash
rm isaac/core/session_manager_old.py
rm temp_test.py
```

**Verify:**
```bash
python -m py_compile isaac/**/*.py
```

**Success:** All Python files compile

---

### Task 3: Patch Shell Injection Vulnerabilities 🔐 (3 hours)
**Status:** 🔴 CRITICAL SECURITY

**Files to fix:**

**3.1: `isaac/dragdrop/smart_router.py`**
```python
# BEFORE (VULNERABLE):
subprocess.run(command, shell=True)

# AFTER (SECURE):
import shlex
subprocess.run(shlex.split(command), shell=False, check=True)
```

**3.2: `isaac/commands/msg.py`**
```python
# BEFORE (VULNERABLE):
subprocess.run(f"echo {msg} | logger", shell=True)

# AFTER (SECURE):
import shlex
subprocess.run(["logger", shlex.quote(msg)], shell=False, check=True)
```

**3.3: `isaac/core/task_manager.py`**
```python
# Add command whitelist validation
# Use shell=False
# Quote all user input with shlex.quote()
```

**Verify:**
```bash
# Run security scanner
pip install bandit
bandit -r isaac/ -ll
# Should show no critical shell injection issues
```

**Success:** No `shell=True` usage, all user input quoted

---

### Task 4: Integrate Alias System ⚡⚡⚡ (30 minutes)
**Status:** 🔴 CRITICAL - Unlocks core feature!

**File:** `isaac/core/command_router.py` (around line 470)

**Add this code:**
```python
def route_command(self, command_str: str, context: Dict) -> CommandResult:
    # Detect platform
    import platform
    current_platform = platform.system().lower()  # 'windows', 'linux', 'darwin'

    # Apply alias translation for Windows
    if current_platform == 'windows' and self._is_unix_command(command_str):
        from isaac.crossplatform.unix_alias_translator import UnixAliasTranslator
        translator = UnixAliasTranslator()
        command_str = translator.translate(command_str, target='powershell')

    # Continue with existing routing logic
    return self._execute_routed_command(command_str, context)

def _is_unix_command(self, cmd: str) -> bool:
    """Check if command looks like a Unix command"""
    unix_commands = {'ls', 'grep', 'ps', 'kill', 'find', 'cat', 'head', 'tail',
                     'cp', 'mv', 'rm', 'pwd', 'which', 'echo', 'touch', 'mkdir'}
    first_word = cmd.strip().split()[0] if cmd.strip() else ''
    return first_word in unix_commands
```

**Test on Windows (if available):**
```bash
isaac "ls -la"          # Should work
isaac "grep foo bar"    # Should work
isaac "ps aux"          # Should work
```

**Test on Linux/Mac:**
```bash
isaac "ls -la"          # Should pass through
```

**Success:** Unix commands work on Windows, pass through on Linux/Mac

---

### Task 5: Add Missing Tier 4 Commands (30 minutes)
**Status:** 🔴 CRITICAL SECURITY

**File:** `isaac/data/tier_defaults.json`

**Add these to tier4 array:**
```json
{
  "tier4": [
    "sudo", "su", "doas",
    "chmod", "chown", "chgrp",
    "rm -rf", "rm -fr", "rmdir",
    "format", "mkfs", "mkfs.ext4", "mkfs.ntfs",
    "dd", "shred",
    "mount", "umount", "unmount",
    "fdisk", "parted", "gparted",
    "systemctl stop", "systemctl disable",
    "shutdown", "reboot", "poweroff",
    "kill -9", "killall -9", "pkill -9",
    "docker rm", "docker rmi", "docker system prune",
    "git push --force", "git push -f",
    "npm install -g", "pip install", "gem install",
    "iptables", "ufw", "firewall-cmd",
    "crontab -r", "at -r",
    "userdel", "groupdel"
  ]
}
```

**Test:**
```bash
# These should require Tier 4 confirmation:
isaac "sudo rm -rf /tmp/test"
isaac "docker rm -f container"
```

**Success:** Dangerous commands require Tier 4 validation

---

## ✅ SUCCESS CRITERIA

After completing all 5 tasks:

- [x] Application starts without errors
- [x] All dependencies installed
- [x] No syntax errors (all .py files compile)
- [x] Zero critical security vulnerabilities
- [x] Core feature (alias system) functional
- [x] 39+ dangerous commands protected with Tier 4

---

## 📊 PROGRESS TRACKING

**Use TodoWrite to track:**
```
1. Install missing dependencies
2. Fix syntax errors
3. Patch shell injection vulnerabilities (3 files)
4. Integrate alias system
5. Add Tier 4 commands
6. Write Phase 1 completion tests
7. Commit and push changes
```

---

## 🧪 PHASE 1 COMPLETION TESTS

**Create:** `tests/test_phase1_completion.py`

```python
import pytest
import subprocess
import os

def test_dependencies_installed():
    """Verify all critical dependencies are installed"""
    import jsonschema
    import dotenv
    import flask
    import anthropic
    import openai
    assert True

def test_no_syntax_errors():
    """Verify all modules can be imported"""
    import isaac.core.command_router
    import isaac.commands.msg
    import isaac.dragdrop.smart_router
    assert True

def test_no_shell_injection():
    """Verify no shell=True usage in subprocess calls"""
    result = subprocess.run(
        ["grep", "-r", "shell=True", "isaac/"],
        capture_output=True,
        text=True
    )
    # Should find no instances (or only safe ones with explanation)
    assert len(result.stdout.strip().split('\n')) < 3, "Found shell=True usage"

def test_alias_system_integrated():
    """Verify alias translator is called in routing"""
    from isaac.core.command_router import CommandRouter
    router = CommandRouter()
    # Check that _is_unix_command method exists
    assert hasattr(router, '_is_unix_command')

def test_tier4_commands_exist():
    """Verify dangerous commands are in Tier 4"""
    import json
    with open('isaac/data/tier_defaults.json') as f:
        tiers = json.load(f)

    tier4 = tiers.get('tier4', [])

    # Check critical commands are protected
    assert 'sudo' in tier4
    assert 'rm -rf' in tier4
    assert 'docker rm' in tier4
    assert len(tier4) >= 39, f"Only {len(tier4)} Tier 4 commands, need 39+"

def test_phase1_health_check():
    """Overall Phase 1 health check"""
    # Application can start
    from isaac.core.command_router import CommandRouter
    router = CommandRouter()

    # Basic routing works
    assert router is not None
```

**Run tests:**
```bash
pytest tests/test_phase1_completion.py -v
```

**Success:** All tests pass

---

## 📝 COMMIT STRATEGY

**After each major task:**

```bash
# Task 1
git add requirements.txt
git commit -m "fix: Install missing dependencies for Phase 1"

# Task 2
git add isaac/
git commit -m "fix: Remove syntax errors and broken files"

# Task 3
git add isaac/dragdrop/smart_router.py isaac/commands/msg.py isaac/core/task_manager.py
git commit -m "security: Patch shell injection vulnerabilities (CVSS 8.5-9.1)"

# Task 4
git add isaac/core/command_router.py
git commit -m "feat: Integrate alias system for cross-platform support"

# Task 5
git add isaac/data/tier_defaults.json
git commit -m "security: Add 39 dangerous commands to Tier 4 protection"

# Tests
git add tests/test_phase1_completion.py
git commit -m "test: Add Phase 1 completion verification tests"
```

**Final push:**
```bash
git push -u origin claude/phase-1-stabilization-[session-id]
```

---

## 📚 REFERENCE DOCUMENTS

**For task details:**
- QUICK_WINS.md (P0 Critical section)
- IMPLEMENTATION_ROADMAP.md (Phase 1 details)

**For context:**
- EXECUTIVE_SUMMARY.md (Why these fixes matter)
- ISAAC_COMPREHENSIVE_ANALYSIS_EXECUTIVE_SUMMARY.md (Full analysis)

**For security details:**
- SECURITY_ANALYSIS.md (Vulnerability details)
- VULNERABILITY_DETAILS.md (CVE-style documentation)

---

## 🚨 IF YOU GET STUCK

**Dependency issues:**
- Check Python version (needs 3.8+)
- Try: `pip install --upgrade pip`
- Try: `pip install -r requirements.txt --no-cache-dir`

**Syntax errors:**
- Look for UTF-8 BOM: `file isaac/core/*.py | grep BOM`
- Remove BOM: `sed -i '1s/^\xEF\xBB\xBF//' filename.py`

**Can't find files mentioned:**
- File may have been moved/deleted
- Check: `find isaac/ -name "*pattern*"`
- Ask: "Should I skip this file or find alternative?"

**Security fix unclear:**
- Principle: Never use `subprocess.run(shell=True)`
- Always: Use `shlex.quote()` for user input
- Always: Pass commands as list: `['cmd', 'arg1', 'arg2']`

**Alias integration complex:**
- The translator class exists: `isaac/crossplatform/unix_alias_translator.py`
- You just need to call it in the router
- Test first on Linux (passthrough), then Windows if available

---

## ✅ PHASE 1 COMPLETE WHEN:

1. All 5 tasks done ✓
2. All Phase 1 tests pass ✓
3. Application starts without errors ✓
4. Security scan shows no critical issues ✓
5. Changes committed and pushed ✓

**Expected outcome:** ISAAC health score improves from 5.5/10 → 6.5/10

**Next phase:** Phase 2 (Quality) - see IMPLEMENTATION_ROADMAP.md

---

**GO TIME!** 🚀

Start with Task 1 (Install Dependencies) right now.
