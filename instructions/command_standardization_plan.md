# Isaac Command Standardization Plan

## Goal
Standardize all Isaac commands to use `-`/`--` flag syntax for clarity and consistency with CLI conventions.

## Current State Analysis
- **Mixed syntax**: Some commands use flags (`/status -v`), others use positional args (`/mine list`)
- **Inconsistency**: `/config status` vs `/status -v` for similar concepts
- **User preference**: Clear `-`/`--` prefixes make options obvious

## Proposed Standardized Syntax

### Core Commands
```
/help [command]              # Show help (unchanged)
/status [--verbose]          # Status with optional verbose flag
/clear                       # Clear screen (unchanged)
/exit, /quit                 # Exit (unchanged)
```

### Config Commands
```
/config [--status]           # System status check
/config [--ai]               # AI provider details
/config [--cloud]            # Cloud sync status
/config [--plugins]          # List plugins
/config [--set <key> <val>]  # Change setting
```

### Mine Commands
```
/mine [--list]               # List all collections
/mine [--use <name>]         # Switch active collection
/mine [--cast <file>]        # Upload file to collection
/mine [--dig <query>]        # Search active collection
/mine [--create <name>]      # Create new collection
/mine [--delete <name>]      # Delete collection
/mine [--info]               # Show collection details
```

### Alias Commands
```
/alias [--list]              # List aliases
/alias [--show <cmd>]        # Show alias details
/alias [--enable]            # Enable aliases
/alias [--disable]           # Disable aliases
/alias [--add <unix> <ps>]   # Add custom alias
/alias [--remove <unix>]     # Remove custom alias
```

## Implementation Strategy

### Phase 1: Core Infrastructure
- Update command router to support flag parsing
- Add argparse wrapper for Isaac commands
- Create flag parsing utility functions

### Phase 2: Command Updates (Priority Order)
1. `/status` (already partially done)
2. `/config` (high usage)
3. `/mine` (high usage)
4. `/alias` (new feature)
5. Others as needed

### Phase 3: Testing & Documentation
- Update all tests
- Update help system
- Update command examples

## Backward Compatibility
- Maintain old syntax during transition with deprecation warnings
- Provide migration guide
- Gradual rollout to avoid breaking user workflows

## Benefits
- **Clarity**: `-list` clearly indicates an option vs positional argument
- **Consistency**: All commands follow same pattern
- **Familiarity**: Matches standard CLI conventions
- **Extensibility**: Easy to add new flags without syntax conflicts

## Files to Modify
- `isaac/core/command_router.py` (add flag parsing)
- `isaac/commands/*/run.py` (update each handler)
- `tests/test_*_commands.py` (update tests)
- Help/documentation files