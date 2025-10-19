# Isaac PowerShell Port - Analysis and Porting Plan

## Original Project Analysis

### Core Architecture (Linux Version)
- **Python-based intelligent shell wrapper** for bash/Linux
- **AI-powered command validation** using Grok-3 via OpenAI API
- **Dual modes**: Shell mode (jr) and Chat mode (cm)
- **Session persistence** with command history
- **File system monitoring** using watchdog library
- **Safety features** for risky commands

### Key Linux Dependencies to Replace
1. **readline** - Command history (Linux-specific)
2. **bash-specific commands** - cd, ls, grep, dpkg, etc.
3. **ANSI color codes** - Terminal styling
4. **File paths** - Unix-style paths (~/.config/isaac)
5. **subprocess.run with shell=True** - Bash command execution

---

## PowerShell Port Strategy

### Phase 1: Core Adaptation
**Goal**: Get basic command validation working in PowerShell

#### Changes Needed:
1. **Replace readline** → Use PowerShell's built-in history (Get-History, Add-History)
2. **Replace subprocess** → Use PowerShell-specific execution
3. **Update file paths** → Windows-style paths ($env:APPDATA\isaac)
4. **Replace ANSI codes** → PowerShell color formatting
5. **Update risky command patterns** → PowerShell dangerous commands

#### PowerShell-Specific Risks:
```python
RISKY_PATTERNS = [
    r'Remove-Item.*-Recurse.*-Force',
    r'Format-Volume',
    r'Clear-Disk',
    r'Remove-Computer',
]
```

### Phase 2: Command Translation Layer
**Challenge**: AI needs to understand PowerShell syntax vs bash

#### System Prompt Update:
- Change from bash/Linux commands to PowerShell equivalents
- Examples:
  - `ls` → `Get-ChildItem` or `dir`
  - `cd` → `Set-Location`
  - `mkdir` → `New-Item -ItemType Directory`
  - `rm` → `Remove-Item`

### Phase 3: History Management
**Replace readline with PowerShell history**

```python
# Instead of readline:
import pyreadline3  # Windows alternative
# OR
# Use PowerShell cmdlet wrapper
```

### Phase 4: File Monitoring
**Keep watchdog** - it works cross-platform, but test on Windows

### Phase 5: Config Location
**Update paths**:
- Linux: `~/.config/isaac/`
- Windows: `$env:APPDATA\isaac\` → `C:\Users\{user}\AppData\Roaming\isaac\`

---

## Implementation Plan

### Quick Win: Minimal Viable Port
1. Strip out readline (use basic input())
2. Change file paths to Windows
3. Update subprocess to handle PowerShell
4. Test basic command execution
5. Get AI validation working

### Full Port: Feature Complete
1. Implement PowerShell history management
2. Add PowerShell-specific command patterns
3. Update AI system prompt for PowerShell syntax
4. Test file monitoring on Windows
5. Add PowerShell safety checks
6. Implement chat mode
7. Test multi-user roles

---

## Key Questions Before Starting

1. **API Choice**: Keep Grok-3 or switch to Claude API?
   - Original uses x.ai/Grok
   - Could port to Anthropic/Claude
   
2. **PowerShell Depth**: 
   - Basic commands only?
   - Or full PowerShell cmdlet support?

3. **Features to Keep/Drop**:
   - Keep: Command validation, chat mode, history, monitoring
   - Drop: Multi-agent system? (sarah agent)
   - Add: PowerShell-specific features?

4. **Execution Method**:
   - Run as Python script calling PowerShell?
   - Or port entirely to PowerShell (native .ps1)?

---

## Suggested Next Steps

1. **Create isaac_powershell.py** - Start with minimal viable port
2. **Test basic execution** - Can it validate and run simple PowerShell commands?
3. **Iterate on AI prompts** - Tune for PowerShell syntax
4. **Add features back** - Once core works, add history, monitoring, etc.

---

## Handoff Suggestion

**This is a refactor/port job**. Suggest:
- Log details to `to_refactor/` for Refactor workspace
- OR log to `to_yaml_maker/` if you want step-by-step implementation specs

What's your call - want to start with a quick minimal port, or map out the full feature set first?
