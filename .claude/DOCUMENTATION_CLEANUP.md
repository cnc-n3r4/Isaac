# Documentation Cleanup - October 22, 2025

## What We're Keeping (Active Development)

### Core Architecture & Data Flow
- ✅ **ISAAC_PIPING_ARCHITECTURE.md** - Active, piping system design
- ✅ **ISAAC_COMMAND_REFERENCE.md** - Active, complete command guide
- ✅ **ISAAC_PROMPT_MODEL.md** - Active, UI specification
- ✅ **DOCUMENTATION_INDEX.md** - Active, navigation

### Implementation Specs (Ready to Build)
- ✅ **piping_system_phase1.md** - Active, needs implementation
- ✅ **piping_system_implementation.md** - Active, step-by-step code
- ✅ **unix_aliases_phase2.md** - Active, needs implementation
- ✅ **PROMPT_MODEL_CORRECTION.md** - Active, critical for coding agents

### Data Flow & Cloud
- ✅ **xai_collections_integration.md** - Active, Collections caching
- ✅ Need to create: Data flow map
- ✅ Need to create: Cloud caching architecture

## What We're Archiving (Old System)

### Outdated Status Docs
- ⚠️ **COMPLETE_PROJECT_STATUS.md** - OLD, Isaac 1.0 status, archive
- ⚠️ **PIPING_SYSTEM_READY.md** - Redundant with PIPING_ARCHITECTURE.md

### Historical Design Docs
- ⚠️ **VISUAL_20251018_isaac_design_session.md** - Historical, archive
- ⚠️ **ui_simplification.md** - Superseded by PROMPT_MODEL.md
- ⚠️ **ISAAC_UI_SPECIFICATION.md** - OLD conversational UI, needs rewrite or archive
- ⚠️ **ISAAC_FINAL_DESIGN.md** - OLD architecture, superseded
- ⚠️ **ISAAC_AI_INTERACTION_DESIGN.md** - OLD patterns, superseded

### Old Implementation Specs
- ⚠️ **ask_command_implementation.md** - COMPLETE, archive
- ⚠️ **collections_config_update.md** - COMPLETE, archive
- ⚠️ **command_queue_overlay_spec.md** - OLD spec, may not be relevant
- ⚠️ **file_operation_logging_integration.md** - OLD spec, unclear status
- ⚠️ **unified_dispatcher_spec.md** - OLD spec, unclear status

### Old Track Docs
- ⚠️ **TRACK1_LOCAL_QOL.md** - Historical
- ⚠️ **TRACK1.2_QUICK_START.md** - Historical
- ⚠️ **TRACK4_AI_INTEGRATION_SPEC.md** - COMPLETE, archive

## New Documentation to Create

### 1. Data Flow Map
**File:** `.claude/bible/ISAAC_DATA_FLOW.md`

**Contents:**
- User → Isaac → Cloud flow diagram
- Local caching strategy
- Collections as cloud cache
- News digest workflow example
- Cron job → Collections → Query pattern

### 2. Cloud Caching Architecture
**File:** `.claude/bible/ISAAC_CLOUD_ARCHITECTURE.md`

**Contents:**
- xAI Collections as primary cache
- Semantic search advantages
- Data retention policies
- Cost optimization (cache vs real-time)
- Sync patterns

### 3. Phase 3 & 4 Specs (Minimal)
**File:** `.claude/mail/to_implement/piping_phases_3_4.md`

**Contents:**
- Phase 3: `/translate`, `/extract`, `/compare` (brief spec)
- Phase 4: `/format`, `/chart`, `/alert` (brief spec)
- Future work, not priority

## Recommended Actions

### Archive Old Docs
Move to `.claude/archive/`:
- COMPLETE_PROJECT_STATUS.md
- VISUAL_20251018_isaac_design_session.md
- ui_simplification.md
- ISAAC_UI_SPECIFICATION.md (needs rewrite)
- ISAAC_FINAL_DESIGN.md
- ISAAC_AI_INTERACTION_DESIGN.md
- All TRACK*.md files
- Completed implementation specs

### Keep Active
- ISAAC_PIPING_ARCHITECTURE.md (THE architecture doc)
- ISAAC_COMMAND_REFERENCE.md (THE command guide)
- ISAAC_PROMPT_MODEL.md (THE UI spec)
- DOCUMENTATION_INDEX.md (update to reflect new structure)
- piping_system_phase1.md (next implementation)
- xai_collections_integration.md (cloud caching foundation)

### Create New
- ISAAC_DATA_FLOW.md (visual diagrams + caching patterns)
- ISAAC_CLOUD_ARCHITECTURE.md (your cloud service integration)

## New Lean Structure

```
.claude/
├── bible/
│   ├── ISAAC_PIPING_ARCHITECTURE.md      # Main architecture
│   ├── ISAAC_COMMAND_REFERENCE.md        # Command guide
│   ├── ISAAC_PROMPT_MODEL.md             # UI specification
│   ├── ISAAC_DATA_FLOW.md                # NEW - Data flow maps
│   └── ISAAC_CLOUD_ARCHITECTURE.md       # NEW - Cloud caching
├── mail/
│   ├── to_implement/
│   │   ├── piping_system_phase1.md       # Next priority
│   │   ├── unix_aliases_phase2.md        # After phase 1
│   │   ├── piping_phases_3_4.md          # NEW - Brief future specs
│   │   └── PROMPT_MODEL_CORRECTION.md    # Critical for agents
│   └── to_yaml_maker/
│       └── piping_system_implementation.md  # Step-by-step code
├── status/
│   └── CURRENT_FOCUS.md                  # NEW - What's active now
├── archive/
│   └── [old docs moved here]
└── DOCUMENTATION_INDEX.md                # Updated navigation
```

## Priority: What to Create Now

1. **ISAAC_DATA_FLOW.md** - Your news digest workflow needs this
2. **ISAAC_CLOUD_ARCHITECTURE.md** - Collections caching patterns
3. **CURRENT_FOCUS.md** - Simple status: Phase 1 next, Phase 2 after

Everything else either exists or can wait.

---

**This gives you a lean, focused documentation set for:**
- Building the piping system
- Implementing cloud caching workflows
- Running cron jobs (news digest, etc.)
- Using Collections as your data cache

**No more old Isaac 1.0 references cluttering things up.**
