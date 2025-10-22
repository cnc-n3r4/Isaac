# Quick Session Log - Isaac Multi-Platform Design

**Session:** vis_20251018_isaac_port
**Workspace:** VISUALIZER
**Project:** isaac
**Date:** 2025-10-18
**Time:** Session Duration ~2 hours

---

## Discussion Summary

### Grand Vision Context
- **Isaac** = Shell assistant prototype for roaming session engine
- **Sarah** = Future conversational AI agent (Jethro Office workspace integration)
- **Matthew** = Coding bot (future)
- **Daniel** = Research/debug bot with omniscient technical logging access
- Isaac serves as root key/gatekeeper for entire agent ecosystem
- Sarah sees everything EXCEPT Isaac's private AIQUERY conversations
- Daniel sees all technical/command data but NOT casual AI queries

### Core Isaac Architecture Designed

**Roaming Session System:**
- Multi-platform (PowerShell + bash) shell assistant
- Cloud-based session persistence via GoDaddy hosting (PHP API)
- JSON file storage for roaming data
- Google Drive initially considered, pivoted to hosted API for better control
- Sessions roam seamlessly across machines (Windows/Linux)
- Machine-aware history tracking

**Isaac as Permanent Shell Layer:**
- NOT a prefix command - Isaac wraps the entire shell experience
- Launch once (`isaac --start`), then all commands route through Isaac
- Natural language routing with context awareness
- Rejects natural language WITHOUT "isaac" prefix ("I have a name, use it")

**Command Tier System (4 Tiers + 2.5):**
- **Tier 1**: Instant execution (ls, cd, pwd) - no AI overhead
- **Tier 2**: Auto-correct typos, auto-execute (grep, etc.)
- **Tier 2.5**: Correct typos, confirm before execute (find, sed, awk)
- **Tier 3**: AI validation required (cp, mv, git commands)
- **Tier 4**: Lockdown with extra warnings (rm -rf, format, dd)
- User-customizable tier assignments (default conservative)
- Config-based auto-run mode (on/off for Tier 2 behavior)

**Task Mode (Multi-Step Command Sequences):**
- Goal-based instruction → AI plans steps → conditional execution
- Safety-based approval strategies:
  - Autonomous: All Tier 1-2 steps (read-only)
  - Approve-once: Contains Tier 3 (show plan, single y/n)
  - Step-by-step: Contains Tier 4 (confirm risky steps individually)
- Interactive failure recovery: (f/r/s/a/?) options
  - **f** = Auto-fix (apply learned fix)
  - **r** = Retry (same command)
  - **s** = Skip (continue to next step, warn if dependencies broken)
  - **a** = Abort (stop task, show summary, offer rollback)
  - **?** = Suggest (Isaac offers alternatives with execution modes)
- Suggestion execution modes:
  - Instant: Execute immediately (num)
  - Confirm: Show command first (num:c)
  - Plan: Insert as new step (num:p)
- Immutable task history (failures logged, fixes append as new steps)

**Auto-Fix Learning System:**
- Isaac learns from user corrections during task failures
- Patterns stored in `learned_autofixes.json` (cloud-synced)
- Cross-platform intelligence (translates fixes between PowerShell/bash)
- Machine-specific compatibility tracking
- Failed fixes on different machines → user choice:
  - (m) Mark machine-specific (keep for others)
  - (d) Disable globally
  - (r) Retry with different fix
- Confidence scoring (0.6 → 1.0 based on success rate)
- User can test/re-enable disabled fixes per machine

**Dual History Architecture:**
- **Command History** (machine-aware):
  - Local cache: Last 100 commands from THIS machine
  - Arrow keys cycle through local cache only
  - Cloud storage: All commands from all machines
  - Excludes AI queries from arrow-key recall
- **AI Query History** (machine-agnostic):
  - Separate log, not in arrow-key history
  - Access via `isaac --show-queries`
  - PRIVATE (user + Isaac only, even Daniel can't see)
  - Tracks machine metadata but displays all together

**Session Data Structure (6 Cloud JSON Files):**
1. **preferences.json**: User settings, tier overrides, API config, behavior flags
2. **command_history.json**: All shell commands (machine-tagged, typed by tier)
3. **aiquery_history.json**: AI conversations (PRIVATE, machine-agnostic)
4. **task_history.json**: Multi-step task logs (immutable, append-only)
5. **learned_autofixes.json**: Auto-fix patterns (cross-platform, machine compatibility)
6. **learned_patterns.json**: Command preferences, usage stats

**Versioning & Rollback System:**
- Keep last 3 auto-snapshots (rolling retention)
- Manual snapshots retained for 30 days
- Rollback triggers:
  - Time-based: Every 2 hours active use
  - Change-based: Every 50 commands
  - Manual: `isaac --snapshot "description"`
  - Pre-rollback: Safety snapshot before revert
  - Machine switch: When changing computers
- Rollback process:
  1. Create safety snapshot
  2. Restore version files from cloud
  3. Write restart marker
  4. Exit Isaac (manual restart required)
  5. Skip splash on warm restart
  6. Option to undo rollback via safety snapshot
- Version metadata tracks: timestamp, machine, changes, SHA256, size

**Terminal UI Design:**
- Splash screen on cold start:
  - "would you like to play... a game?" (War Games reference)
  - "nah!!" centered
  - ASCII art "Isaac" in figlet
  - Colored acronym (Intelligent System Agent And Control)
  - Locks top 3 lines as persistent header
- Header layout (read-only theater):
  - Line 1: Isaac's processing/responses (streams, truncates at width)
  - Line 2: Warnings/alternatives/metadata (wraps if needed)
  - Line 3: Status indicators (fixed format, never wraps)
- Status symbols: `[✓✓]` = AI online + synced, `[✓~]` = AI online + sync pending, etc.
- Terminal flow below header: Natural user>isaac>user>isaac stack
- All interaction happens in terminal (header is display-only)

**Offline Mode:**
- Shell mode degrades gracefully (commands execute, no AI validation)
- Chat mode disabled (requires AI)
- Queue commands locally in `~/.isaac/offline_queue.json`
- Auto-reconnect ping every 60 seconds
- Batch upload queued messages when connection restored
- Prompt indicator: `isaac [OFFLINE]>`

---

## Decisions Made

### Architecture
- ✅ **GoDaddy PHP API** over Google Drive for session storage (better control, no sync conflicts)
- ✅ **Hybrid data model**: JSON for roaming, SQLite for future Jethro integration
- ✅ **Isaac as permanent shell layer** (not prefix command)
- ✅ **Machine-aware command history**, agnostic AI query history
- ✅ **Versioning with rollback** (last 3 snapshots + manual)
- ✅ **Manual restart required** after rollback (guarantees clean reload)
- ✅ **Warm restart detection** (skip splash screen after rollback/config changes)

### User Experience
- ✅ **Natural language requires "isaac" prefix** (reject without prefix)
- ✅ **5-tier command system** (1, 2, 2.5, 3, 4) with user customization
- ✅ **Config-based auto-run mode** for Tier 2 typo corrections
- ✅ **Task mode with smart approval** (autonomous/approve-once/step-by-step based on tier mix)
- ✅ **Interactive failure recovery** with auto-fix/retry/skip/abort/suggest
- ✅ **Suggestion execution modes** (instant/confirm/plan) with tier-aware defaults
- ✅ **Immutable task history** (failures stay visible, fixes append)
- ✅ **AI queries invisible to arrow-key history** (separate log, access via flag)

### Learning & Intelligence
- ✅ **Auto-fix learning from user corrections** (manual intervention → saved pattern)
- ✅ **Cloud-sync learned fixes** (roam with session)
- ✅ **Machine-specific compatibility tracking** (disable failed fixes per machine)
- ✅ **Cross-platform fix translation** (PowerShell ↔ bash equivalent actions)
- ✅ **Command preference learning** (track follow-up patterns)

### Privacy & Security
- ✅ **Isaac's AIQUERY conversations = PRIVATE** (user-only, hidden from all agents)
- ✅ **Sarah can USE Isaac** (execute commands) but NOT READ Isaac's logs
- ✅ **Daniel sees all technical data** (commands, tasks, API metadata) but NOT casual AI queries
- ✅ **Isaac = root key/gatekeeper** for entire agent ecosystem (opaque to others)

### Future Jethro Integration
- ✅ **Isaac lives outside Jethro DB** (session data in cloud, not shared with other bots)
- ✅ **Sarah/Matthew/Daniel in Jethro SQLite** (workspace-bound agents)
- ✅ **Isaac provides VTT shell execution** for Jethro bots (AIC panel integration)
- ✅ **Separate API keys** per agent (no sharing)

---

## Concerns/Blockers

### Technical Challenges (Not Blockers, Just Noted)
- **Cross-platform shell abstraction**: PowerShell vs bash syntax differences (next design session)
- **Startup sequence mechanics**: Terminal control, header locking, splash timing (next design session)
- **Offline queue merging**: How to handle conflicts if multiple machines go offline simultaneously (edge case, defer)
- **GoDaddy shared hosting limits**: PHP execution time, file I/O constraints (test in MVP)
- **Version file storage growth**: Cleanup strategy needs definition (manual for MVP, cron later)

### Design Questions Still Open
- **PowerShell vs bash abstraction layer**: How does Isaac detect shell and translate commands?
- **Startup sequence implementation**: Header locking mechanics, splash screen timing
- **Offline mode reconnection**: Retry logic, exponential backoff, user notification

### Non-Issues (Addressed)
- ~~Google Drive sync conflicts~~ → Solved with hosted API
- ~~Dual-write complexity~~ → Cloud is single source of truth
- ~~History divergence~~ → Machine-aware tracking prevents conflicts
- ~~Auto-fix cross-machine compatibility~~ → Machine-specific disable option

---

## Next Session Pickup

### Immediate Focus (Choose One)
1. **PowerShell vs bash shell abstraction**
   - Shell detection on startup
   - Command translation layer
   - Tier list variations per shell
   - Cross-platform learned fix application

2. **Startup sequence implementation**
   - Splash screen timing and mechanics
   - Header locking (top 3 lines)
   - Terminal control (clear, cursor positioning)
   - Warm vs cold start detection
   - Status line updates (streaming)

3. **Offline mode behavior**
   - Queue management (local storage)
   - Reconnection logic (ping intervals, backoff)
   - Batch sync on reconnect
   - Conflict resolution (if queue diverges)

### Action Items for Implementation
1. **Session Data Structure**: All 6 JSON schemas fully defined ✅
2. **API Endpoints**: PHP micro-API design (save_session, get_session, sync_all)
3. **Versioning System**: Snapshot triggers, rollback flow, cleanup policy
4. **Terminal UI**: Header layout, status symbols, prompt design
5. **Tier System**: Default tier assignments per command (PowerShell + bash lists)
6. **Task Mode**: Step planning, failure recovery, suggestion system
7. **Learning System**: Auto-fix pattern detection, confidence scoring

### Context Needed for Next Session
- **Shell abstraction**: Isaac needs to know which shell it's wrapping (PowerShell, bash, zsh, fish?)
- **Terminal capabilities**: ANSI codes, cursor control, header locking approach
- **GoDaddy testing**: Validate PHP file I/O speed, execution limits
- **Command whitelist**: Full Tier 1-4 command lists for both shells

---

## Related Files
- **Original Linux Isaac**: `C:\Projects\isaac\isaac_original.py`
- **Porting Notes**: `C:\Projects\isaac\PORTING_NOTES.md`
- **SIM'D Roadmap**: `roadmap.txt` (uploaded during session - agent ecosystem vision)
- **Jethro Project**: `https://github.com/cnc-n3r4/ProMan-Tinktr` (future integration target)

---

## Tags
#isaac #shell-assistant #roaming-sessions #multi-platform #task-mode #auto-fix-learning #godaddy-api #powershell #bash #versioning #rollback #privacy #agent-ecosystem #sim-d #jethro-integration

---

## Session Metrics
- **Design Decisions**: 25+
- **Architecture Components**: 10 major systems
- **Data Structures**: 6 cloud JSON files + versioning metadata
- **User Flows**: Startup, command execution, task mode, rollback, offline mode
- **Privacy Model**: Isaac/Sarah/Daniel access matrix defined
- **Future Integration**: Jethro agent ecosystem connection points mapped

---

**Session Status**: COMPREHENSIVE DESIGN COMPLETE (Core Architecture)

**Remaining Design Work**: Shell abstraction, startup sequence, offline mode

**Implementation Ready**: Session data structure, versioning, task mode, learning system
