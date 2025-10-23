# /mine Command Redesign - Mining Metaphor Overhaul

**Date:** October 23, 2025
**Priority:** HIGH
**Complexity:** MEDIUM-HIGH
**Estimated Time:** 6-8 hours

---

## 🎯 Problem Statement

Current `/mine` commands are confusing and hard to remember:
- `--use`, `--create`, `--cast`, `--dig`, `--pan` don't form a cohesive mental model
- No way to save file_ids locally for targeted searches
- No piping support for file_id management
- Command structure doesn't leverage mining metaphors effectively

## 🏆 Solution: Complete Mining Metaphor Redesign

### New Command Structure (Mining Theme)

**CORE COMMANDS:**
```bash
/mine --list                  # Quick alias to --deed --all (legacy-friendly)
/mine --deed [--all]          # Deed the claim: --all lists everything; no arg shows active details
/mine --stake <name>          # Stake/create new claim (initial plot-out)
/mine --claim <name>          # Claim/use/switch to a staked claim (enter the territory)
/mine --claim <name> --dig <text>  # Claim and dig in one motion
/mine --drift <name>          # Carve/create drift (collection) within active claim
/mine --haul <file>           # Haul file into active drift (or claim's default)
/mine --dig <question>        # Dig answers from active drift/claim
/mine --pan <drift>           # Pan file_ids in a specific drift
/mine --abandon <claim>       # Abandon/delete claim (drifts caved in)
/mine --info                  # Quick alias to --deed (for active only)
```

### File ID Management System

**NEW: Local File ID Storage**
- `/mine --pan <collection> | /config` pipes file_ids to config
- Saves file_ids locally in `~/.isaac/config.json`
- Enables targeted searches within specific files
- `/config --console` can display/manage saved file_ids

**Config Structure:**
```json
{
  "xai": {
    "collections": {
      "file_ids": [
        "file_01852dbb-3f44-45fc-8cf8-699610d17501",
        "file_01934abc-5f55-4gfd-9h9h-700720d17602"
      ],
      "search_files_only": true
    }
  }
}
```

---

## 📋 Implementation Plan

### Phase 1: Command Redesign (3-4 hours)

**1. Update Command Parser** (`isaac/commands/mine/run.py`)
- Replace flag-based routing with new mining commands
- Add backward compatibility aliases
- Update help text with mining metaphors

**2. New Handler Methods:**
```python
def _handle_stake(self, args):      # Create collection
def _handle_claim(self, args):      # Switch collection
def _handle_drift(self, args):      # Create sub-collection (future)
def _handle_haul(self, args):       # Upload file
def _handle_deed(self, args):       # List/show collections
def _handle_abandon(self, args):    # Delete collection
```

**3. Backward Compatibility:**
- Keep old flags working with deprecation warnings
- Map old commands to new mining equivalents:
  - `--create` → `--stake`
  - `--use` → `--claim`
  - `--cast` → `--haul`
  - `--list` → `--deed --all`

### Phase 2: File ID Piping System (2-3 hours)

**1. Enhanced /config Command** (`isaac/commands/config/run.py`)
- Add piping support: `stdin` input processing
- Parse file_id lists from `/mine --pan` output
- Save to config with validation
- Display current file_ids

**2. /mine --pan Output Format**
- Structure output for easy parsing
- JSON format option for piping
- Human-readable format for direct viewing

**3. Config Integration**
- Add `file_ids` array to collections config
- `/mine --dig` respects `search_files_only` flag
- Filter searches to specified file_ids only

### Phase 3: Testing & Polish (1 hour)

**1. Test Scenarios:**
```bash
# New mining commands
/mine --stake myMusic
/mine --claim myMusic
/mine --haul song.mp3
/mine --dig "find rock songs"
/mine --pan myMusic | /config
/mine --dig "specific lyrics"  # Uses saved file_ids

# Backward compatibility
/mine --create oldStyle        # Still works, shows deprecation
/mine --use oldStyle --dig "test"  # Still works
```

---

## 🔄 Migration Strategy

**Immediate (No Breaking Changes):**
- Add new commands alongside old ones
- Old commands work with deprecation warnings
- New commands take precedence

**Gradual (1-2 weeks):**
- Update documentation to show new commands
- User training through examples
- Remove old commands after adoption

**Future (Post-Adoption):**
- Clean up old command handlers
- Simplify codebase with single command set

---

## 🎨 Mining Metaphor Details

**Claim:** Top-level collection (like a mining claim)
- `--stake`: Mark territory for mining
- `--claim**: Work this claim (switch to it)
- `--abandon`: Give up the claim

**Drift:** Sub-collection within a claim (tunnel in the mine)
- `--drift`: Carve a new tunnel for specialized mining
- Future: Organize content by topic/type

**Operations:**
- `--haul`: Bring ore (files) into the mine
- `--dig`: Extract valuable ore (search for answers)
- `--pan`: Sift through dirt to find gold nuggets (file_ids)
- `--deed`: Legal record of your claims

---

## 📊 Benefits

✅ **Intuitive:** Mining metaphors are memorable and logical
✅ **Powerful:** File ID targeting enables precise searches
✅ **Compatible:** Backward compatibility eases transition
✅ **Extensible:** Drift system ready for future organization features
✅ **Pipelined:** Full piping support for automation

---

## 🚧 Dependencies

- xAI SDK (already integrated)
- Config system (already exists)
- Piping infrastructure (Phase 1 complete)

---

## ✅ Success Criteria

- [ ] All new mining commands implemented
- [ ] File ID piping works: `/mine --pan coll | /config`
- [ ] Backward compatibility maintained
- [ ] Targeted searches work with saved file_ids
- [ ] Help text updated with mining theme
- [ ] All tests pass

---

**Ready for implementation!** 🚀</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_implement\mine_command_redesign_mining_metaphor.md