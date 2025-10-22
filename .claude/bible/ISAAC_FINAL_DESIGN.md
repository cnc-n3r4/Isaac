# Isaac Multi-Platform Design - Final Summary

**Session:** vis_20251018_isaac_port  
**Workspace:** VISUALIZER  
**Project:** isaac  
**Date:** 2025-10-21 (Updated)  
**Status:** ✅ CORE ARCHITECTURE COMPLETE + VISION INTEGRATION

---

## What We Built

A **comprehensive design specification** for Isaac - a personal, cloud-synced AI shell companion with dual modes, personality, safety validation, and cross-device continuity.

---

## Command Structure Reference

**ALL internal Isaac commands use `/` slash prefix:**
- `/help`, `/config`, `/status`, `/ask <query>`, `/task <goal>`, `/msg`, `/collect`, `/debug`
- `/clear`, `/exit`, `/quit`

**Device routing uses `!` bang:**
- `/msg !laptop2 "message"` - Send message to specific device
- `/show-cmd !desktop3` - View command history from another device

**Natural language alternative:**
- `isaac <query>` - Works in both external and internal modes
- Inside Isaac shell, `/ask <query>` is the standard form

---

## Complete Architecture Overview

### 1. Dual Mode System
- **External CLI Mode**: Quick commands like `isaac /ask <query>` or `isaac /msg !desktop3`. Lightweight, no shell takeover.
- **Internal Shell Mode**: `isaac /start` takes over terminal, becoming primary interface with full meta-commands and AI validation.
- **Switching**: Seamless transition, prompt changes (`C:\ >` to `$>`).

### 2. Cloud Continuity & Sync
- **Backbone**: GoDaddy hosted PHP API for shared data.
- **Continuity**: Ongoing chat session across OS/terminals via cloud memories.
- **Data Separation**: Local (command history per device), Cloud (AI memories, collections, messages).
- **Sync**: Background with configurable intervals, offline queuing.
- **xAI Integration**: Optional collections for broader AI scope.

### 3. Command System
- **Meta-Commands**: `/ask`, `/config`, `/collect`, `/debug`, `/msg`, `/f` (force), `/task`—extensible plugins.
- **External Mode**: Limited commands for safety (`isaac /ask`, `isaac /move`, `isaac /start`).
- **Internal Mode**: Full command set with `/` prefix.
- **Force Command**: `/f <cmd>` bypasses tier validation (internal-only for safety).
- **Personality**: Sass for invalid inputs ("I have a name, use it."), helpful for queries, playful confirmations ("saved your dumbass").
- **Routing**: Device routing with `!` prefix (`/msg !laptop2`), validity checks, tier validation.

### 4. AI & Context
- **Queries**: `/ask <query>` (internal mode standard) or `isaac <query>` (works in both modes).
- **Memory**: Cloud-stored conversations, remembers across devices.
- **Collections**: Cloud file groups for AI analysis.
- **Debugging**: Upload files, async AI feedback.

### 5. Safety & Validation
- **Tier System**: 1-4 with AI confirmations for risky commands.
- **Personality in Safety**: Sass confirmations ("saved your dumbass").
- **Learning**: Auto-fixes from user corrections, cross-platform.

### 6. Roaming Session System
- **Storage:** 6 cloud-synced JSON files per user.
- **Platforms:** Windows (PowerShell) + Linux (bash/zsh/fish).
- **Multi-machine:** Simultaneous sessions, device-tagged data.
- **Sync:** Immediate command sync, no conflicts.

### 7. Task Mode (Multi-Step Automation)
- **Input:** External: `isaac /task <description>`, Internal: `/task <description>`
- **Planning:** AI breaks into steps with logic.
- **Execution:** Autonomous/approve modes based on tiers.
- **Recovery:** 5 options (auto-fix/retry/skip/abort/suggest).

### 8. Dual History Architecture
**Command History (Machine-Aware):**
- Local cache: Last 100 commands per device.
- Cloud storage: All commands, accessible via `/show-cmd !device`.

**AI Query History (Machine-Agnostic):**
- Cloud-stored, private, cross-device recall.

### 9. Session Data Structure (6 Cloud Files)
```
1. preferences.json          - Settings, tier overrides, API config
2. command_history.json      - All shell commands (device-tagged)
3. aiquery_history.json      - AI conversations (PRIVATE)
4. task_history.json         - Multi-step task logs
5. learned_autofixes.json    - Auto-fix patterns
6. collections.json          - Cloud file groups
```

### 10. Terminal UI Design
**External Mode:**
```
C:\ > isaac /ask where is alaska?
Alaska is in the northwest...
```

**Internal Mode (Splash on Start):**
```
would you like to play... a game? → nah!!
[Isaac ASCII art]
Total time: ~5.5 seconds

$> ls
[output]
$> /ask where is alaska?
[response]
$> /config
[config interface]
```

**Header (Internal Mode):**
```
Line 1: PowerShell 7.3.0 | DESKTOP-WIN11
Line 2: Session loaded (1247 commands)
Line 3: [✓✓ ONLINE | SYNCED] ───────────────────
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Scroll region]
isaac> Ready.
user> _
```

### 11. Offline Mode
- **Behavior:** Commands execute without AI, queue for sync.
- **Indicator:** `isaac [OFFLINE]>` prompt.

---

## Privacy & Agent Ecosystem Integration

### Isaac's Role (Root Key)
- **Gatekeeper:** API keys, unlocks other agents.
- **Privacy:** AI queries private from all agents.

### Sarah (Future - Office Agent)
- **Access:** Uses Isaac as tool, sees results only.

### Daniel (Future - Debug Bot)
- **Access:** Technical data, not casual queries.

---

## Command Examples

### External Mode
```bash
C:\ > isaac /ask where is alaska?
up north (or whatever it responds)

C:\ > isaac /move those files i was working on earlier all to the cloud  
done! (and then whatever proof or validation would be appropriate)

C:\ > isaac /start
[isaac starts in output window, takes over shell as interface]
```

### Internal Mode  
```bash
$> ls
[lists files like normal]

$> where is alaska?
[system error because 'where' is a valid command and that wasn't a valid input]

$> isaac where is alaska?
[isaac response, no matter how short or long]

$> how many species of bird are there?
I have a name, use it.

$> isaac how many species of birds are there?
[isaac response, no matter how short or long]

$> /ask how many species of birds are there?
[isaac response, no matter how short or long. same as using 'isaac' internally]

$> rm C:\user\all-my-personal-stuff-folder
[level 3] do you really want to remove this? (y/n)
$> n
saved your dumbass

$> /f rm C:\user\all-my-personal-stuff-folder2
done!

$> /msg !laptop2 "dont forget to copy that stuff"
done. message queued on cloud. when you login from laptop2, you will get this message.

$> /config
[loads config stuff]

$> /collect the projectB folder  
done. ProjectB folder uploaded to 'codingstuff' collection.
type /collect --help for more information on /collect command.

$> /exit
Isaac's outtie 5000 ! See ya!
```

### External Mode Restrictions
```bash
C:\ > isaac what is warmer california or florida?
type 'isaac /help' for help.
to make a general query, use 'isaac /ask'.

C:\ > isaac /f rm C:\user\all-my-personal-stuff-folder
internal isaac command not authorized for external use.
type 'isaac /help' for help.
to use full isaac implementation use 'isaac /start' first.

C:\ > isaac /ask what is warmer california or florida?
isaac> depends where, what time of year.. yada yada yada
```

### Tasks & Learning
```bash
$> /task backup files                 # Multi-step (internal mode)
$> /show-cmd !laptop2                 # View other device's history
```

---

## Implementation Priority

### Phase 1 (MVP - Core Modes)
1. ✅ Dual mode system (external/internal)
2. ✅ Cloud sync with separation (local/cloud)
3. Shell detection & abstraction
4. Basic meta-commands (`/ask`, `/config`)
5. Personality engine (sass for invalid inputs)
6. Command routing with validity checks

### Phase 2 (Intelligence & Continuity)
1. AI integration with context memory
2. Tier system with confirmations
3. Task mode
4. Collections & debugging
5. Cross-device sync

### Phase 3 (Advanced Features)
1. Offline queuing
2. Auto-fix learning
3. Versioning & rollback
4. Full command set expansion

### Phase 4 (Ecosystem)
1. Agent integrations (Sarah, Daniel)
2. Multi-user support (if needed)

---

## Design Decisions Log

### Major Choices Made
- ✅ Dual modes for flexibility
- ✅ Cloud continuity with local caching
- ✅ Personality for engaging UX
- ✅ Command validity checks for routing
- ✅ Cloud-shared AI memories, local command history
- [Existing decisions from original doc]

### Open Questions
- Offline sync conflict resolution
- xAI collection upload frequency
- Command cache size limits

---

## Next Steps

### For Implementation
1. Build mode switching in CommandRouter
2. Implement cloud sync with data separation
3. Add personality responses
4. Expand meta-command system

### For Design
1. Offline behavior details
2. Collection management UI
3. Agent integration specs

---

## Files & References

[Same as original]

---

## Acknowledgments

**Updated Vision:** Integrated dual modes, cloud continuity, personality, and expanded commands.

**Status:** READY FOR IMPLEMENTATION

---

**END OF DESIGN SPECIFICATION**
