# Isaac Documentation Index
**Last Updated:** October 22, 2025  
**Purpose:** Master navigation for all Isaac design and implementation documentation

---

## 📚 The Bible - Authoritative Design Docs

These are the single source of truth. When in doubt, check here first.

### Core Architecture
- **[ISAAC_FINAL_DESIGN.md](./bible/ISAAC_FINAL_DESIGN.md)** - Overall system architecture, command flow, tier system
- **[ISAAC_UI_SPECIFICATION.md](./bible/ISAAC_UI_SPECIFICATION.md)** - Terminal UI design, header layout, status indicators
- **[ISAAC_AI_INTERACTION_DESIGN.md](./bible/ISAAC_AI_INTERACTION_DESIGN.md)** - AI integration patterns, validation logic

### Feature Specifications
- **[ISAAC_PIPING_ARCHITECTURE.md](./bible/ISAAC_PIPING_ARCHITECTURE.md)** - Complete piping system design (5,500+ words)
  - Hybrid shell/Isaac piping philosophy
  - Data blob format and transformations
  - Plugin interface specification
  - Unix alias system (Phase 2)
  - 4-phase implementation roadmap

- **[ISAAC_COMMAND_REFERENCE.md](./bible/ISAAC_COMMAND_REFERENCE.md)** - Complete command guide
  - All commands with examples
  - Mining metaphor (/mine cast, /mine dig)
  - Piping integration patterns
  - Configuration files
  - Learning path and testing guide

### Design History
- **[VISUAL_20251018_isaac_design_session.md](./bible/VISUAL_20251018_isaac_design_session.md)** - Original design session log
- **[ui_simplification.md](./bible/ui_simplification.md)** - UI simplification instructions
- **[decision flow chart.md](./bible/decision%20flow%20chart.md)** - Command classification and execution swimlane

---

## 📋 Implementation Specs - Ready to Build

These are detailed specifications ready for coding agents.

### Active Work (Phase 1 - Piping System)
- **[piping_system_phase1.md](./mail/to_implement/piping_system_phase1.md)** - Phase 1 requirements
  - PipeEngine module spec
  - Shell adapter stdin support
  - Essential commands: /save, /analyze, /summarize
  - Test requirements
  - **Estimate:** 8-12 hours, Medium complexity

### Next Phase (Phase 2 - Unix Aliases)
- **[unix_aliases_phase2.md](./mail/to_implement/unix_aliases_phase2.md)** - Phase 2 requirements
  - UnixAliasTranslator module
  - 15+ common aliases (grep→Select-String, etc.)
  - Command router fallback hook
  - **Estimate:** 6-8 hours, Low-Medium complexity
  - **Depends on:** Phase 1 complete

### Completed Tracks
- **[TRACK4_AI_INTEGRATION_SPEC.md](./mail/to_implement/TRACK4_AI_INTEGRATION_SPEC.md)** - AI integration (COMPLETE)
  - `/ask` command with session memory ✅
  - `/mine` command with Collections ✅
  - xAI grok-3 model integration ✅

- **[xai_collections_integration.md](./mail/to_implement/xai_collections_integration.md)** - Collections integration details
  - API architecture (Chat vs Collections Management)
  - Chain query pattern design
  - Collection management commands

---

## 🛠️ Implementation Guides - Step-by-Step Code

These have complete code ready to execute. No placeholders.

### Piping System
- **[piping_system_implementation.md](./mail/to_yaml_maker/piping_system_implementation.md)** - Complete implementation guide
  - 7 implementation steps with full code
  - Step 1: Shell adapter stdin support
  - Step 2: PipeEngine module (complete code)
  - Step 3: Command router pipe detection
  - Steps 4-6: /save, /analyze, /summarize commands (yaml + run.py)
  - Step 7: Test suite
  - Manual test commands
  - **Ready for:** YAML Maker or Implement persona

---

## 📊 Status & Progress Tracking

Current state of the project across all tracks and phases.

### Overall Status
- **[COMPLETE_PROJECT_STATUS.md](./status/COMPLETE_PROJECT_STATUS.md)** - Overall project progress
- **[PIPING_SYSTEM_READY.md](./status/PIPING_SYSTEM_READY.md)** - Piping system executive summary and handoff
  - Command examples (shell→Isaac, Isaac→shell, mixed)
  - Success metrics and acceptance criteria
  - Implementation phases breakdown
  - Risk assessment

### Track Status (Historical)
- **[TRACK1_QUICK_START.md](./TRACK1_QUICK_START.md)** - Initial setup and quick start
- **[TRACK1.2_QUICK_START.md](./TRACK1.2_QUICK_START.md)** - Enhanced quick start

---

## 📬 Persona Mailboxes - Collaboration System

Handoff notes between personas in the ISAAC-1 team.

### For Coding Agents
- `./mail/to_yaml_maker/` - Ready-to-implement specs with complete code
- `./mail/to_implement/` - Implementation specifications
- `./mail/to_refactor/` - Code quality and architectural improvements
- `./mail/to_debug/` - Bug reports and issue tracking
- `./mail/to_test/` - Validation requirements and test strategy

### For Design & Management
- `./mail/to_visual/` - Design discussions, architecture decisions (Sarah)
- `./mail/to_tracker/` - Project coordination, progress monitoring

---

## 📝 Session Logs - Historical Context

Conversation history and decision rationale from all personas.

**Location:** `./logs/`

These contain session history useful for understanding:
- What's been tried
- Decisions made and why
- Context from other personas
- Evolution of design thinking

---

## 🗂️ Flow Documentation - Decision Diagrams

Detailed command flow and decision trees.

**Location:** `./bible/flow/`

### Command Orchestration
- **[00_overview.md](./bible/flow/00_overview.md)** - High-level flow overview
- **[01_classification.md](./bible/flow/01_classification.md)** - Command classification logic
- **[02_execution_logging.md](./bible/flow/02_execution_logging.md)** - Execution and chronological logging
- **[03_user_confirmation.md](./bible/flow/03_user_confirmation.md)** - User confirmation workflow
- **[04_ai_validation.md](./bible/flow/04_ai_validation.md)** - AI validation decision flow

---

## 🧭 Quick Navigation by Task

### "I need to understand the system"
1. Start: [ISAAC_FINAL_DESIGN.md](./bible/ISAAC_FINAL_DESIGN.md)
2. Then: [ISAAC_COMMAND_REFERENCE.md](./bible/ISAAC_COMMAND_REFERENCE.md)
3. Deep dive: [ISAAC_PIPING_ARCHITECTURE.md](./bible/ISAAC_PIPING_ARCHITECTURE.md)

### "I need to implement piping system"
1. Overview: [PIPING_SYSTEM_READY.md](./status/PIPING_SYSTEM_READY.md)
2. Requirements: [piping_system_phase1.md](./mail/to_implement/piping_system_phase1.md)
3. Code guide: [piping_system_implementation.md](./mail/to_yaml_maker/piping_system_implementation.md)
4. Architecture: [ISAAC_PIPING_ARCHITECTURE.md](./bible/ISAAC_PIPING_ARCHITECTURE.md)

### "I need to learn the commands"
1. Complete reference: [ISAAC_COMMAND_REFERENCE.md](./bible/ISAAC_COMMAND_REFERENCE.md)
2. Examples in context: [ISAAC_PIPING_ARCHITECTURE.md](./bible/ISAAC_PIPING_ARCHITECTURE.md)
3. Test examples: [piping_system_phase1.md](./mail/to_implement/piping_system_phase1.md)

### "I need to understand AI integration"
1. Design: [ISAAC_AI_INTERACTION_DESIGN.md](./bible/ISAAC_AI_INTERACTION_DESIGN.md)
2. Implementation: [TRACK4_AI_INTEGRATION_SPEC.md](./mail/to_implement/TRACK4_AI_INTEGRATION_SPEC.md)
3. Collections: [xai_collections_integration.md](./mail/to_implement/xai_collections_integration.md)

### "I need to work on UI"
1. Specification: [ISAAC_UI_SPECIFICATION.md](./bible/ISAAC_UI_SPECIFICATION.md)
2. Simplification notes: [ui_simplification.md](./bible/ui_simplification.md)
3. Flow integration: [./bible/flow/](./bible/flow/)

---

## 📦 Command Quick Reference

### Mining Commands (Personal File History)
```bash
/mine cast <file>              # Upload to Collections (was upload)
/mine dig <question>           # Search with AI (was query)
/mine use <name>               # Switch collection
/mine ls                       # List collections
/mine init <name>              # Create collection
```

### AI Commands
```bash
/ask <question>                # Chat with AI (has memory)
```

### Piping Commands (Phase 1 - In Development)
```bash
<cmd> | /save <file>           # Save output
<cmd> | /analyze [prompt]      # AI analysis
<cmd> | /summarize [length]    # Condense text
```

### Hybrid Piping Examples
```bash
ls | /save dir.txt                          # Shell → Isaac
/mine dig "errors" | grep "404" | wc -l     # Isaac → Shell → Shell
cat log | /analyze | grep "important"       # Shell → Isaac → Shell
```

---

## 🎯 Current Focus

**Active Work:** Phase 1 - Hybrid Piping System  
**Status:** Design complete, ready for implementation  
**Next Persona:** YAML Maker or Implement  
**Estimate:** 8-12 hours

**What's Ready:**
- ✅ Complete architectural specification
- ✅ Step-by-step implementation guide with full code
- ✅ Test requirements and acceptance criteria
- ✅ All command names finalized (mining metaphor)
- ✅ Documentation cohesive and consistent

**What's Needed:**
- Execute 7 implementation steps from guide
- Create PipeEngine module
- Add stdin support to shell adapters
- Implement /save, /analyze, /summarize commands
- Write test suite
- Validate acceptance criteria

---

## 📖 Naming Conventions

### Mining Metaphor
Consistent imagery for `/mine` commands:
- **cast** - Casting ore down the shaft (uploading)
- **dig** - Digging up insights (querying)
- **use** - Switch mines (collection context)
- **ls** - List mines (collections)
- **init** - Open new mine (create)

### Backward Compatibility
Old names work as aliases:
- `/mine upload` → routes to `cast`
- `/mine query` → routes to `dig`

### Why These Names?
- Shorter (cast=4, dig=3 vs upload=6, query=5)
- Memorable (cohesive metaphor)
- Intuitive (action matches purpose)
- Composable (works in pipes)

---

## 🔧 Development Workflows

### Setup
```bash
pip install -e .                           # Install Isaac
isaac /start                               # Launch shell
```

### Testing
```bash
pytest tests/ --cov=isaac --cov-report=term     # Full suite
pytest tests/test_tier_validator.py -v          # Specific test
```

### Configuration
```bash
/config ai on                              # Enable AI
/config cloud off                          # Disable sync
/status                                    # Check status
```

---

## 📚 File Organization

```
.claude/
├── DOCUMENTATION_INDEX.md          # This file - master navigation
├── bible/                           # Authoritative design docs
│   ├── ISAAC_FINAL_DESIGN.md
│   ├── ISAAC_PIPING_ARCHITECTURE.md
│   ├── ISAAC_COMMAND_REFERENCE.md
│   ├── ISAAC_UI_SPECIFICATION.md
│   └── ISAAC_AI_INTERACTION_DESIGN.md
├── mail/                            # Persona collaboration
│   ├── to_implement/               # Specs ready to build
│   ├── to_yaml_maker/              # Step-by-step guides
│   ├── to_refactor/                # Quality improvements
│   ├── to_debug/                   # Bug tracking
│   ├── to_test/                    # Test strategy
│   ├── to_visual/                  # Design discussions
│   └── to_tracker/                 # Progress monitoring
├── status/                          # Current project state
│   ├── COMPLETE_PROJECT_STATUS.md
│   └── PIPING_SYSTEM_READY.md
└── logs/                            # Session history
```

---

## 🎓 Learning Resources

### For New Users
1. Read: [ISAAC_COMMAND_REFERENCE.md](./bible/ISAAC_COMMAND_REFERENCE.md) - Learning Path section
2. Try: `/ask`, `/mine`, basic piping
3. Explore: Hybrid commands once Phase 1 launches

### For Developers
1. Architecture: [ISAAC_FINAL_DESIGN.md](./bible/ISAAC_FINAL_DESIGN.md)
2. Implementation: [piping_system_implementation.md](./mail/to_yaml_maker/piping_system_implementation.md)
3. Testing: `tests/` directory and TEST_EXECUTION_GUIDE.md

### For Designers
1. Design philosophy: [VISUAL_20251018_isaac_design_session.md](./bible/VISUAL_20251018_isaac_design_session.md)
2. UI specification: [ISAAC_UI_SPECIFICATION.md](./bible/ISAAC_UI_SPECIFICATION.md)
3. Flow diagrams: [./bible/flow/](./bible/flow/)

---

**Document Syncing:** This directory syncs to Google Drive for mobile access.  
**Updates:** When design decisions finalize, bible docs get updated first, then implementation specs.  
**Questions:** Check bible docs first, then status docs, then ask Visual persona.
