# Isaac Cross-Platform Development Guide

## Overview

Isaac is now set up for simultaneous Linux and Windows development on a shared NAS.

**NAS Location:**
- **Linux:** `~/isaac-nas` (symlink) or `/run/user/1000/gvfs/smb-share:server=ls220d759,share=share/ISAAC`
- **Windows:** `Z:\` (or your mapped drive letter)
- **IP:** 192.168.12.10 (ls220d759)

---

## Architecture Benefits

### Why This Setup Works

1. **Shared Codebase** - One source of truth on NAS
2. **Platform-Specific Testing** - Test on both OS simultaneously
3. **Dual Claude Code** - Two AI assistants helping with same code
4. **Instant Sync** - Changes appear immediately on both sides
5. **No Git Conflicts** - Git stays local, only code is shared

---

## Development Scenarios

### Scenario 1: Linux Primary Development

**Use Case:** You primarily develop on Linux, occasionally test on Windows

**Workflow:**
```bash
# On Linux
cd ~/isaac-nas
source /home/birdman/Projects/Isaac/venv/bin/activate  # Use local venv
code .  # Or use Claude Code

# Make changes...
# Files instantly available on Windows

# Test on Windows when needed
# Switch to Windows machine, open Z:\, test
```

**Benefits:**
- Fast Linux development
- Windows available for testing
- No manual sync needed

---

### Scenario 2: Windows Primary Development

**Use Case:** You primarily develop on Windows, occasionally test on Linux

**Workflow:**
```powershell
# On Windows
cd Z:\
.\venv\Scripts\activate
code .  # Or use Claude Code

# Make changes...
# Files instantly available on Linux

# Test on Linux when needed
# SSH into Linux, cd ~/isaac-nas, test
```

**Benefits:**
- Native Windows development
- Linux available for verification
- Instant feedback

---

### Scenario 3: Simultaneous Debugging (Advanced)

**Use Case:** Debug platform-specific issues on both OS at once

**Linux Claude Code Session:**
```bash
cd ~/isaac-nas
# Focus on: Bash adapter, Linux-specific commands, /mine integration
```

**Windows Claude Code Session:**
```powershell
cd Z:\
# Focus on: PowerShell adapter, Windows-specific commands, path handling
```

**Coordination:**
- Use code comments to communicate
- Test cross-platform features together
- Both Claude Code sessions can help debug

**Example:**
```python
# Linux Claude: Fixed bash command execution
# Windows Claude: Please test PowerShell equivalent

def execute_command(cmd):
    # Both AIs working on same function
    pass
```

---

## Critical Rules

### ✅ DO

1. **Keep venv separate**
   - Linux venv: `/home/birdman/Projects/Isaac/venv` (local)
   - Windows venv: `Z:\venv` (on NAS, Windows-specific)

2. **Keep .git local**
   - Linux git: `/home/birdman/Projects/Isaac/.git`
   - Windows git: Local clone (not on NAS)

3. **Share source code only**
   - Python files, configs, docs
   - Cross-platform compatible code

4. **Test on both platforms**
   - File operations (pathlib compatibility)
   - Command execution (bash vs PowerShell)
   - Path handling (/ vs \)

### ❌ DON'T

1. **Don't share venv** - Platform-specific binaries won't work
2. **Don't put .git on NAS** - Git database is fragile over SMB
3. **Don't edit same file simultaneously** - Can cause conflicts
4. **Don't assume paths** - Use pathlib.Path for cross-platform

---

## Testing Strategy

### Platform-Specific Tests

**Linux Only:**
```bash
# Test bash adapter
python -c "from isaac.adapters.bash_adapter import BashAdapter; print('OK')"

# Test Unix paths
python test_ai_router.py
```

**Windows Only:**
```powershell
# Test PowerShell adapter
python -c "from isaac.adapters.powershell_adapter import PowerShellAdapter; print('OK')"

# Test Windows paths
python test_ai_router.py
```

### Cross-Platform Tests

**Both Platforms:**
```python
# Test AI routing (should work everywhere)
from isaac.ai import IsaacAgent
agent = IsaacAgent()
result = agent.chat("Hello")
print(result['response'])

# Test file tools (pathlib ensures compatibility)
from isaac.tools import ReadTool, WriteTool
read_tool = ReadTool()
result = read_tool.execute(file_path="README.md", limit=10)
print(result['content'])
```

---

## Code Guidelines for Cross-Platform

### Paths
```python
# ✅ GOOD - Cross-platform
from pathlib import Path

file_path = Path("~/data/file.txt").expanduser()
config_dir = Path.home() / ".isaac"

# ❌ BAD - Platform-specific
file_path = "/home/user/data/file.txt"  # Linux only
file_path = "C:\\Users\\user\\data\\file.txt"  # Windows only
```

### Command Execution
```python
# ✅ GOOD - Use adapters
from isaac.adapters.shell_detector import ShellDetector

shell = ShellDetector.detect()
result = shell.execute("ls" if shell.name == "bash" else "dir")

# ❌ BAD - Platform-specific
os.system("ls -la")  # Linux only
```

### File Operations
```python
# ✅ GOOD - Use Isaac tools
from isaac.tools import ReadTool

tool = ReadTool()
result = tool.execute(file_path="config.json")

# ❌ BAD - Direct file ops without Path
with open("/etc/config.json") as f:  # Linux only
    data = f.read()
```

---

## Git Workflow

### Recommended Setup

**Linux (Primary Git Repository):**
```bash
cd /home/birdman/Projects/Isaac  # Local, not NAS
git init
git remote add origin <your-remote>

# Work flow:
# 1. Edit files on NAS (~/isaac-nas)
# 2. Copy changes to local git repo
# 3. Commit and push
cp -r ~/isaac-nas/* .
git add .
git commit -m "Changes from NAS development"
git push
```

**Windows (Optional Git Clone):**
```powershell
cd C:\Projects
git clone <your-remote> Isaac

# Work flow:
# 1. Edit files on NAS (Z:\)
# 2. Pull changes from remote
cd C:\Projects\Isaac
git pull
# 3. Copy to NAS for testing
robocopy . Z:\ /MIR /XD .git venv
```

---

## Troubleshooting

### "Cannot access NAS"

**Linux:**
```bash
# Check mount
mount | grep smb

# Reconnect if needed
# Usually auto-mounts via GVFS when you access it in file manager
nautilus /run/user/1000/gvfs/
```

**Windows:**
```powershell
# Check connection
net use

# Reconnect if needed
net use Z: \\192.168.12.10\share\ISAAC /persistent:yes
```

### "Import errors after switching platforms"

**Cause:** Wrong venv activated or no venv

**Solution:**
```bash
# Linux
cd ~/isaac-nas
source /home/birdman/Projects/Isaac/venv/bin/activate

# Windows
cd Z:\
.\venv\Scripts\activate
```

### "File permission errors"

**Cause:** SMB doesn't support Unix permissions

**Solution:** Ignore permission errors on SMB mounts. Files work fine, just can't set chmod.

### "Claude Code can't find files"

**Cause:** Path issues or NAS not mounted

**Solution:**
- Linux: Verify `~/isaac-nas` exists and works
- Windows: Verify `Z:\` is accessible
- Check NAS is online: `ping 192.168.12.10`

---

## Performance Tips

### Faster Development

1. **Use local venv** (Linux) for faster imports
2. **Cache tools** - Don't reinstall packages repeatedly
3. **Test locally first** before cross-platform testing
4. **Use SSD** - NAS over network is slower than local

### Network Optimization

- **Wired connection** > WiFi for NAS access
- **Close unused files** in editors (less file watching)
- **Disable auto-sync** in editors if too slow
- **Local git** > network git (always use local .git)

---

## Best Practices

### 1. Coordinate Claude Code Sessions

**Before starting:**
- Decide which platform for which task
- Leave comments for other session
- Don't edit same file simultaneously

**Example workflow:**
```python
# Linux Claude Code working on AI routing
# TODO for Windows Claude: Test PowerShell integration

class AIRouter:
    # Linux session focus here
    pass
```

### 2. Platform-Specific Branches

If doing major platform work:
```bash
# On Linux
git checkout -b linux-bash-improvements

# On Windows
git checkout -b windows-powershell-improvements

# Merge when stable
```

### 3. Testing Checklist

Before committing cross-platform code:
- [ ] Works on Linux
- [ ] Works on Windows
- [ ] Uses pathlib.Path for paths
- [ ] Uses shell adapters for commands
- [ ] No hardcoded platform assumptions

### 4. Documentation

Always document platform-specific behavior:
```python
def execute_command(cmd):
    """
    Execute shell command
    
    Platform behavior:
    - Linux: Uses bash
    - Windows: Uses PowerShell
    - Automatically detected via ShellDetector
    """
    pass
```

---

## Example Cross-Platform Session

### Day 1: Linux Primary

**Morning - Linux Claude Code:**
```bash
cd ~/isaac-nas
source /home/birdman/Projects/Isaac/venv/bin/activate

# Work on AI routing improvements
# Claude helps implement new features
# Test on Linux
python test_ai_router.py
```

**Afternoon - Test on Windows:**
```powershell
# Switch to Windows machine
cd Z:\
.\venv\Scripts\activate

# Test same features
python test_ai_router.py

# Note any Windows-specific issues
# Comment in code for next session
```

### Day 2: Windows Debugging

**Morning - Windows Claude Code:**
```powershell
cd Z:\
# Claude helps fix Windows-specific bugs
# Fix PowerShell adapter issues
```

**Afternoon - Verify on Linux:**
```bash
cd ~/isaac-nas
# Test that Windows fixes didn't break Linux
python test_ai_router.py
```

---

## Advanced: Triple-Platform Development

If you want to test on macOS too:

1. **Mac:** Mount SMB share
   ```bash
   open smb://192.168.12.10/share/ISAAC
   ```

2. **Create Mac venv**
   ```bash
   cd /Volumes/ISAAC
   python3 -m venv venv-mac
   source venv-mac/bin/activate
   pip install -r requirements.txt
   ```

3. **Test Mac-specific**
   - Similar to Linux (Unix-based)
   - But may have different shell behavior
   - Test path handling

---

## Summary

✅ **What Works:**
- Shared source code on NAS
- Instant sync between platforms
- Separate platform-specific venvs
- Dual Claude Code sessions
- Cross-platform testing

✅ **What to Remember:**
- Always use pathlib.Path
- Keep .git local
- Separate venvs per platform
- Test on both before committing
- Coordinate Claude Code sessions

✅ **Result:**
- Robust cross-platform codebase
- Fast development on preferred platform
- Easy testing on other platforms
- Professional multi-OS support

---

*Last Updated: November 8, 2025*
*For Windows-specific setup, see WINDOWS_SETUP.md*
