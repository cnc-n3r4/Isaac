# Implementation: Data Files

## Goal
Create static data files that core modules depend on (tier_defaults.json, splash_art.txt, help_text.txt).

**Time Estimate:** 10 minutes

**Dependencies:** 02_impl_bootstrap.md (directory structure must exist)

---

## File 1: tier_defaults.json

**Path:** `isaac/data/tier_defaults.json`

**Purpose:** Default command tier assignments for 5-tier safety system.

**Complete File:**
```json
{
  "1": [
    "ls", "dir", "cd", "pwd", "echo", "cat", "type", "whoami",
    "Get-ChildItem", "Set-Location", "Get-Location", "Write-Output",
    "hostname", "date", "time", "clear", "cls"
  ],
  "2": [
    "grep", "Select-String", "head", "tail", "wc", "sort", "uniq",
    "awk", "cut", "tr"
  ],
  "2.5": [
    "find", "sed", "Where-Object", "Select-Object", "ForEach-Object"
  ],
  "3": [
    "cp", "mv", "git", "npm", "pip", "apt", "yum", "brew",
    "Copy-Item", "Move-Item", "Install-Package", "Update-Package",
    "mkdir", "touch", "New-Item", "chmod", "chown"
  ],
  "4": [
    "rm", "del", "Remove-Item", "format", "Format-Volume", "dd",
    "mkfs", "fdisk", "parted", "sudo rm", "sudo dd"
  ]
}
```

**Explanation:**
- **Tier 1:** Read-only, instant execution (ls, cd, pwd)
- **Tier 2:** Safe utilities, auto-correct typos (grep, head, tail)
- **Tier 2.5:** Text processing, confirm before execute (find, sed, awk)
- **Tier 3:** File operations, package managers (cp, mv, git, npm)
- **Tier 4:** Destructive commands, lockdown warnings (rm, format, dd)

---

## File 2: splash_art.txt

**Path:** `isaac/data/splash_art.txt`

**Purpose:** ASCII art for startup splash screen (WarGames theme).

**Complete File:**
```
 _____ ____    _    _    ____ 
|_ _/ ___|  / \  | |  / ___|
 | |\___ \ / _ \ | | | |    
 | | ___) / ___ \| | | |___ 
|___|____/_/   \_\_|  \____|

Intelligent System Agent And Control
```

**Notes:**
- Total display time: 5.5 seconds (forced, non-skippable)
- Sequence:
  1. "would you like to play... a game?" (1s)
  2. Pause (0.5s)
  3. "nah!!" (1s)
  4. ASCII art + acronym (3s)

---

## File 3: help_text.txt

**Path:** `isaac/data/help_text.txt`

**Purpose:** Help documentation for `isaac --help`.

**Complete File:**
```
Isaac 2.0 - Multi-Platform Shell Assistant
==========================================

USAGE:
  isaac --start              Launch Isaac shell
  isaac --help               Show this help
  isaac --show-log           Show command history (current machine)
  isaac --show-log --all     Show command history (all machines)
  isaac --machines           List all active machines
  isaac --versions           List available snapshots (Phase 2)
  
INTERACTIVE COMMANDS:
  exit                       Quit Isaac
  quit                       Quit Isaac
  help                       Show this help
  
COMMAND TIERS:
  Tier 1:   Instant execution (ls, cd, pwd)
  Tier 2:   Auto-correct typos (grep, head, tail)
  Tier 2.5: Confirm before execute (find, sed, awk)
  Tier 3:   Validation required (cp, mv, git)
  Tier 4:   Lockdown warnings (rm -rf, format, dd)
  
NATURAL LANGUAGE (Phase 2):
  isaac <query>              AI-powered query (requires API key)
  
CONFIGURATION:
  Config file: ~/.isaac/config.json
  Edit tier assignments, API credentials, preferences
  
EXAMPLES:
  isaac --start              # Launch shell
  ls                         # Tier 1: Executes immediately
  git commit -m "test"       # Tier 3: Prompts for confirmation
  rm -rf folder              # Tier 4: Shows lockdown warning
  
MULTI-MACHINE SYNC:
  Commands automatically sync to cloud after execution.
  Run isaac --show-log --all to see commands from all machines.
  
MORE INFO:
  Documentation: https://github.com/yourusername/isaac
  Issues: https://github.com/yourusername/isaac/issues
```

---

## Verification Steps

### 1. Check Files Exist
```bash
ls isaac/data/
```

**Expected output:**
```
tier_defaults.json
splash_art.txt
help_text.txt
```

### 2. Validate tier_defaults.json
```bash
python -c "import json; print(json.load(open('isaac/data/tier_defaults.json')))"
```

**Expected:** No JSON parse errors, prints tier dictionary

### 3. Test Tier Defaults Loading (Quick Python REPL Test)
```python
import json
from pathlib import Path

tier_file = Path('isaac/data/tier_defaults.json')
tiers = json.loads(tier_file.read_text())

# Check Tier 1 commands
assert 'ls' in tiers['1']
assert 'cd' in tiers['1']
assert 'Get-ChildItem' in tiers['1']  # PowerShell

# Check Tier 4 commands  
assert 'rm' in tiers['4']
assert 'Remove-Item' in tiers['4']  # PowerShell
assert 'format' in tiers['4']

print("✅ Tier defaults validated")
```

### 4. Check Splash Art
```bash
cat isaac/data/splash_art.txt
```

**Expected:** ASCII art displays correctly

### 5. Check Help Text
```bash
cat isaac/data/help_text.txt
```

**Expected:** Help documentation displays

---

## Common Pitfalls

⚠️ **JSON Syntax Errors**
- **Symptom:** `json.decoder.JSONDecodeError`
- **Fix:** Validate JSON with `python -m json.tool isaac/data/tier_defaults.json`

⚠️ **Missing Commands in Tiers**
- **Symptom:** Commands get classified as Tier 3 (unknown default)
- **Fix:** Add command to appropriate tier in tier_defaults.json

⚠️ **Encoding Issues (Windows)**
- **Symptom:** ASCII art displays with weird characters
- **Fix:** Save files as UTF-8 encoding

⚠️ **File Not Found at Runtime**
- **Symptom:** `FileNotFoundError: tier_defaults.json`
- **Fix:** Ensure `package_data` in setup.py includes `*.json` and `*.txt`

---

## Testing Data Files

**Quick test that data files are accessible:**

```python
from pathlib import Path

# Test tier_defaults.json
data_dir = Path(__file__).parent / 'data'
tier_file = data_dir / 'tier_defaults.json'

if tier_file.exists():
    import json
    tiers = json.loads(tier_file.read_text())
    print(f"✅ Loaded {len(tiers)} tiers")
    print(f"   Tier 1 commands: {len(tiers['1'])}")
    print(f"   Tier 4 commands: {len(tiers['4'])}")
else:
    print("❌ tier_defaults.json not found")

# Test splash_art.txt
splash_file = data_dir / 'splash_art.txt'
if splash_file.exists():
    art = splash_file.read_text()
    print(f"✅ Loaded splash art ({len(art)} chars)")
else:
    print("❌ splash_art.txt not found")

# Test help_text.txt
help_file = data_dir / 'help_text.txt'
if help_file.exists():
    help_text = help_file.read_text()
    print(f"✅ Loaded help text ({len(help_text)} chars)")
else:
    print("❌ help_text.txt not found")
```

**Expected output:**
```
✅ Loaded 5 tiers
   Tier 1 commands: 17
   Tier 4 commands: 11
✅ Loaded splash art (182 chars)
✅ Loaded help text (1234 chars)
```

---

## Success Signals

✅ tier_defaults.json created and validates as JSON  
✅ All 5 tiers present (1, 2, 2.5, 3, 4)  
✅ Both PowerShell and bash commands included  
✅ splash_art.txt created and displays correctly  
✅ help_text.txt created  
✅ Files accessible via Path(__file__).parent / 'data'  
✅ Ready for next step (shell adapters)

---

**Next Step:** 04_impl_shell_adapters.md (Create base, PowerShell, bash adapters)

---

**END OF DATA FILES IMPLEMENTATION**
