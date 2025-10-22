# Isaac Terminal UI Specification

**Created:** 2025-10-19  
**Workspace:** VISUALIZER  
**Project:** isaac  
**Status:** ✅ COMPLETE

---

## Purpose

Detailed visual specification for Isaac's terminal interface, including:
- Cold start splash sequence (5.5s forced)
- Locked header layout (4 lines)
- Status indicators and prompt states
- Error handling visualization
- Special screens (help, versions, etc.)

This document defines EXACTLY what users see when interacting with Isaac.

---

## 1. Launch Sequence (Cold Start)

### Phase 1: War Games Reference (2 seconds)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                                                             │
│              Shall we play a game?                          │
│                                                             │
│                      ... nah!!                              │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
- Centered text
- Brief pause for dramatic effect
- Reference to 1983 "WarGames" film

### Phase 2: ASCII Logo (3 seconds)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   _____ _____         _____                                 │
│  |_   _/  ___|  /\   /  __ \                                │
│    | | \ `--.  /  \  | /  \/                                │
│    | |  `--. \/  /\ \| |                                    │
│   _| |_/\__/ /  __  \ \__/\                                 │
│   \___/\____/_/    \_\____/                                 │
│                                                             │
│   Intelligent System Agent And Control                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
- ASCII art "ISAAC" logo
- Full acronym below logo
- Centered display

### Phase 3: Loading Messages (0.5 seconds)
```
Loading session data...
Connecting to cloud storage...
Initializing AI layer...
```
- Simulated loading (actual operations happen async)
- Three dots animation optional
- Quick scroll through

**Total Duration:** 5.5 seconds (NO skip button for MVP)

---

## 2. Terminal Header Layout

### Locked Header (Always Visible - Top 4 Lines)

**Full Layout:**
```
PowerShell 7.3.0 | DESKTOP-WIN11                    [v0.1.0]
Session loaded (1247 commands) | Last sync: 2m ago
[✓✓ ONLINE | SYNCED] ──────────────────────────────────────
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Line-by-Line Breakdown

**Line 1: Environment Info**
```
PowerShell 7.3.0 | DESKTOP-WIN11                    [v0.1.0]
^               ^               ^                   ^
Shell version   Machine name    Padding             Isaac version
```
- Left: Auto-detected shell + version
- Center: Hostname (auto-detected)
- Right: Isaac version (right-aligned)

**Line 2: Session Stats**
```
Session loaded (1247 commands) | Last sync: 2m ago
^                              ^
Machine-local count            Relative timestamp
```
- Left: Command count (THIS machine only)
- Right: Time since last cloud sync

**Line 3: Status Bar**
```
[✓✓ ONLINE | SYNCED] ──────────────────────────────────────
^                    ^
Status indicators    Fill to terminal width
```
- Left: Two-character status (see section 3)
- Right: Decorative dash line (fills remaining space)

**Line 4: Separator**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
- Full-width heavy line (U+2501 character)
- Visual break between header and interaction zone

### Behavior
- **Locked:** Header stays at top during scroll
- **Dynamic:** Line 2 & 3 update in real-time
- **Persistent:** Survives clear-screen commands

---

## 3. Status Indicator States

### Status Symbols

| Symbol | AI Status | Sync Status | Description |
|--------|-----------|-------------|-------------|
| `[✓✓]` | Online | Synced | Normal operation - everything working |
| `[✓~]` | Online | Pending | AI available but local changes not uploaded |
| `[✗✓]` | Offline | Synced | No internet but session data is current |
| `[✗✗]` | Offline | Unsaved | No internet AND unsaved local changes |
| `[⊙⊙]` | Online | Syncing | Active cloud upload in progress |

### Color Coding (Terminal Support Permitting)
- `✓✓` → Green (all systems go)
- `✓~` → Yellow (warning - sync pending)
- `✗✓` → Orange (caution - offline but safe)
- `✗✗` → Red (alert - data at risk)
- `⊙⊙` → Cyan (info - activity in progress)

### Animation (Optional Enhancement)
- `⊙⊙` could rotate through: `⊙○` → `○⊙` → `⊙○` (spinner effect)

---

## 4. Prompt States

### Normal Ready State
```
isaac> Ready.
user> _
```
- `isaac>` = System messages
- `user>` = User input line
- `_` = Cursor position

### After Command Execution
```
user> isaac hello
isaac> Hey! What can I help with?
user> _
```
- Echo user input
- Show Isaac's response
- Return to ready state

### AI Thinking State
```
user> isaac move files from downloads to backup
isaac> 🤔 Translating...
```
- Shows processing indicator
- Brief (usually <1 second)
- Replaced with translation result

### Tier 3 Validation State
```
user> git push origin main
isaac> ⚠️ Tier 3 command detected. AI validating...
      → git push origin main
      Confidence: 95%
      Execute? (y/n): _
```
- Warning symbol
- Shows translated command
- Displays AI confidence level
- Waits for user confirmation

### Task Mode Planning
```
user> /task backup my project files
isaac> 📋 Planning task...
      Step 1/5: Verify source directory exists
      Step 2/5: Create backup folder with timestamp
      Step 3/5: Copy files (excluding .git/)
      Step 4/5: Compress to .tar.gz
      Step 5/5: Upload to cloud storage
      
      Mode: [A]utonomous / [O]nce / [S]tep-by-step? _
```
- Task emoji indicator
- Numbered steps with descriptions
- Mode selection prompt

### Task Execution Progress
```
isaac> ✓ Step 1/5 complete: Directory verified
      → Step 2/5: Creating backup folder...
```
- Checkmark for completed steps
- Arrow for current step
- Real-time progress

---

## 5. Error State Visualization

### Bare Natural Language (Missing "isaac" Prefix)
```
user> hello
isaac> ⊘ I have a name, use it.
      💡 Try: isaac hello
user> _
```
- Prohibition symbol (⊘)
- Friendly reminder message
- Suggestion with correct syntax

### Unknown Command Pattern
```
user> isaac asdfghjkl
isaac> ✗ Unable to translate: asdfghjkl
      💡 Did you mean: isaac --help?
user> _
```
- X symbol for failure
- Shows what it couldn't understand
- Suggests help command

### Translation Failed (Ambiguous Input)
```
user> isaac do the thing
isaac> ✗ I don't understand: "do the thing"
      💡 Try being more specific:
         - isaac backup my documents
         - isaac list command history
         - /task organize my files
user> _
```
- Multiple suggestions
- Examples of clear commands

### Tier 4 Lockdown (Critical Command Blocked)
```
user> rm -rf /
isaac> 🚨 TIER 4 LOCKDOWN 🚨
      Command: rm -rf /
      Risk: CRITICAL - System deletion
      
      This command is BLOCKED.
      💡 If you need to delete files, specify a safe directory.
user> _
```
- Warning emoji
- Shows exact blocked command
- Explains risk level
- Provides safe alternative guidance

### Offline Mode
```
user> isaac translate this command
isaac [OFFLINE]> ✗ AI unavailable (no internet)
                 💡 Command queued for when connection restored
                 💡 Shell commands still work normally
user> _
```
- Modified prompt with `[OFFLINE]` tag
- Explains limitation
- Reassures that basic functionality remains

### Sync Failure
```
isaac> ⚠️ Cloud sync failed (timeout)
      💡 Your data is safe locally
      💡 Will retry automatically in 60s
user> _
```
- Warning but not critical
- Reassurance about data safety
- Automatic retry info

---

## 6. Warm Restart (After Rollback/Config)

### Skip Splash, Show Context
```
PowerShell 7.3.0 | DESKTOP-WIN11                    [v0.1.0]
Session loaded (1247 commands) | Last sync: just now
[✓✓ ONLINE | SYNCED] ──────────────────────────────────────
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

isaac> Restarted after rollback to version 3.
isaac> Session restored from snapshot_20251018_1430.
isaac> Ready.
user> _
```
- No splash screen
- Context message explains why restart happened
- Ready state immediately

### Warm Restart Triggers
- After `isaac --rollback`
- After `isaac --undo-rollback`
- After config changes requiring reload
- After manual `isaac --restart`

---

## 7. Special Screens

### Help Screen (`isaac --help`)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ISAAC - Intelligent System Agent And Control
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXTERNAL MODE (before 'isaac /start'):
  isaac /ask <query>        AI query
  isaac /move <files>       File operations
  isaac /start              Enter internal mode

INTERNAL MODE (after 'isaac /start'):
  /help                     Show available commands
  /config                   Configuration management
  /status                   System status check
  /ask <query>              AI query (or use: isaac <query>)
  /task <description>       Multi-step automation
  /collect <path>           Upload to cloud collections
  /debug --file <file>      AI debugging analysis
  /f <cmd>                  Force execute (bypasses tier validation)
  /msg !device "text"       Message another device
  /show-cmd !device         View device command history
  /clear                    Clear screen
  /exit, /quit              Exit internal mode

NATURAL LANGUAGE:
  isaac <query>             Works in both modes
  
PERSONALITY:
  Invalid queries without 'isaac' get sass: "I have a name, use it."
  Canceled dangerous commands: "saved your dumbass"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Version List (`isaac --versions`)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AVAILABLE VERSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

AUTO SNAPSHOTS (Last 3):
  [3] 2025-10-18 14:30  (347 commands since v2)  ← CURRENT
  [2] 2025-10-18 12:15  (198 commands since v1)
  [1] 2025-10-18 09:00  (Session start)

MANUAL SNAPSHOTS:
  [M1] 2025-10-17 16:45  "Before major refactor"  (expires: 27d)
  [M2] 2025-10-15 11:20  "Stable working state"   (expires: 25d)

USAGE:
  isaac --rollback 2      Restore to auto snapshot 2
  isaac --restore-snapshot M1   Restore to manual snapshot

⚠️  Rollback creates safety snapshot before restore.
💡 Undo with: isaac --undo-rollback

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Machine List (`isaac --machines`)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACTIVE MACHINES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[CURRENT]
  DESKTOP-WIN11 (PowerShell 7.3.0)
  Commands: 1247 | Last active: now

[OTHER MACHINES]
  PARROT-VM (bash 5.1.4)
  Commands: 892 | Last active: 3d ago

  LAPTOP-WORK (PowerShell 5.1)
  Commands: 345 | Last active: 1w ago

TOTAL: 3 machines | 2484 commands across all sessions

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Config Display (`isaac config show`)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEHAVIOR:
  Auto-run Tier 2:     OFF (commands need confirmation)
  Task default mode:   Step-by-step

STORAGE:
  Cloud sync:          Enabled (GoDaddy PHP API)
  Offline queue:       Enabled
  Auto-snapshot:       Every 2h or 50 commands

TIER OVERRIDES:
  find → Tier 1 (instant, was Tier 2.5)
  grep → Tier 1 (instant, was Tier 2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 8. Implementation Notes

### Terminal Requirements
- **Minimum:** 80x24 character terminal
- **Recommended:** 120x40 for comfortable viewing
- **Color support:** Optional but enhances UX
- **Unicode support:** Required for symbols (✓✗⊘⊙🤔📋🚨💡)

### Header Locking Technique
Two approaches depending on platform:
1. **ANSI escape codes:** `\033[H` to return to top
2. **Curses library:** ncurses (Linux) / windows-curses (Windows)

Recommendation: Start with ANSI, migrate to curses for Phase 2.

### Performance Considerations
- Header updates: Max 1/second to avoid flicker
- Status changes: Immediate (critical info)
- Sync timestamp: Update every 10s when idle

### Accessibility
- All symbols have text equivalents
- Color is additive, not required
- Screen reader friendly (prompts are clear text)

---

## 9. Visual Style Guide

### Typography Hierarchy
```
isaac>   System messages (responses, status)
user>    User input line
  →      Current action/step indicator
  ✓      Success/completed
  ✗      Error/failed
  ⊘      Blocked/rejected
  ⚠️      Warning
  🚨     Critical alert
  💡     Tip/suggestion
  🤔     Processing
  📋     Task/planning
  ⊙      Activity/syncing
```

### Indentation Rules
- Base level: No indent
- Suggestions: 3 spaces
- Multi-line output: 6 spaces
- Nested content: +3 spaces per level

### Spacing Rules
- Blank line after Isaac response (before next prompt)
- No blank line within multi-line Isaac output
- Blank line before/after special screens (help, versions)

---

## 10. Edge Cases & Polish

### Terminal Resize
- Header reflows to new width
- Status bar dashes recalculate
- Separator line adjusts length

### Very Long Commands
```
user> isaac move all the files from my downloads folder to my backup drive and compress them into a zip file with today's date
isaac> 🤔 Translating...
      → tar -czf backup_20251018.tar.gz ~/Downloads/*
      → mv backup_20251018.tar.gz /mnt/backup/
      
      This will be executed as 2 commands.
      Continue? (y/n): _
```
- Break long translations into steps
- Show clearly what will happen

### Rapid Commands
```
user> ls
user> pwd
user> cd projects
isaac> ✓ Executed 3 commands
      Currently in: C:\Users\ndemi\projects
user> _
```
- Batch output for Tier 1 commands
- Single summary response

### Session Timeout
```
isaac> ⚠️ Session idle for 30 minutes.
      💡 Cloud sync paused to save bandwidth.
      💡 Type any command to resume.
```
- Friendly reminder after inactivity
- No forced logout (user stays in Isaac)

---

## Summary

This specification defines:
- ✅ 5.5 second splash screen (no skip)
- ✅ 4-line locked header with live updates
- ✅ 5 status indicator states
- ✅ Multiple prompt states (ready, thinking, validating, task)
- ✅ Comprehensive error visualization
- ✅ Warm restart behavior (no splash)
- ✅ Special screens (help, versions, machines, config)
- ✅ Edge case handling

**Status:** COMPLETE - Ready for implementation.

---

**END OF UI SPECIFICATION**
