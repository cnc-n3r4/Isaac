# ISAAC Command Syntax Standardization - Implementation Handoff

## Overview
**Priority:** CRITICAL - User Experience Breaking Change
**Impact:** All ISAAC commands must be updated to require hyphens for ALL arguments
**Deadline:** Immediate - User has demanded this change for clarity

## Current State
- Documentation has been updated to reflect new syntax
- All command examples now use `--flag` format
- No bare arguments or subcommands without hyphens allowed

## Required Changes

### 1. Command Parser (`isaac/core/command_router.py`)
**File:** `isaac/core/command_router.py`

**Current Logic:**
```python
# OLD: Mixed parsing
if input.startswith('/mine cast'):
    # Handle as subcommand
elif input.startswith('/ask'):
    # Handle positional arg
```

**New Logic Required:**
```python
# NEW: Flag-based parsing for ALL commands
def parse_command_flags(command_line):
    """Parse ALL arguments as --flags"""
    # Examples:
    # "/mine --cast file.txt" → {"action": "cast", "file": "file.txt"}
    # "/ask 'what is docker?'" → {"action": "ask", "question": "what is docker?"}
    # "/ask" → {"action": "interactive"}  # or similar for interactive mode
    # "/save --file output.txt" → {"action": "file", "value": "output.txt"}
```

### 2. Command Handlers - Update All

#### `/mine` Command (`isaac/commands/mine.py`)
**Current:** `/mine cast file.txt` (subcommand + positional)
**New:** `/mine --cast file.txt` (action flag + required arg)

**Current:** `/mine dig "query"` (subcommand + positional)  
**New:** `/mine --dig "query"` (action flag + required arg)

**Current:** `/mine use collection` (subcommand + positional)
**New:** `/mine --use collection` (action flag + required arg)

**Current:** `/mine ls` (subcommand only)
**New:** `/mine --ls` (action flag only)

**Current:** `/mine init name` (subcommand + positional)
**New:** `/mine --init name` (action flag + required arg)

#### `/ask` Command (`isaac/commands/ask.py`)
**Current:** `/ask question` (positional arg)
**New:** `/ask` (no arguments - assumes input is a question)

#### `/save` Command (`isaac/commands/save.py`)
**Current:** `/save file.txt` (positional arg)
**New:** `/save --file file.txt` (flag + required arg)

#### `/analyze` Command (`isaac/commands/analyze.py`)
**Current:** `/analyze [prompt]` (optional positional)
**New:** `/analyze [--prompt prompt]` (optional flag + arg)

#### `/summarize` Command (`isaac/commands/summarize.py`)
**Current:** `/summarize [length]` (optional positional)
**New:** `/summarize [--length length]` (optional flag + arg)

#### `/backup` Command (`isaac/commands/backup.py`)
**Current:** `/backup [target]` (optional positional)
**New:** `/backup [--target target]` (optional flag + arg)

#### `/restore` Command (`isaac/commands/restore.py`)
**Current:** `/restore file.zip` (positional arg)
**New:** `/restore --file file.zip` (flag + required arg)

#### `/config` Command (`isaac/commands/config.py`)
**Current:** `/config status` (subcommand)
**New:** `/config --status` (action flag)

**Current:** `/config set key value` (subcommand + positionals)
**New:** `/config --set key value` (action flag + required args)

### 3. Argument Parsing Library
**Recommendation:** Adopt `argparse` or similar for ALL commands

**Example Implementation:**
```python
import argparse

def parse_mine_command(args):
    parser = argparse.ArgumentParser(prog='/mine')
    subparsers = parser.add_subparsers(dest='action', required=True)
    
    # Cast subcommand
    cast_parser = subparsers.add_parser('cast')
    cast_parser.add_argument('--file', required=True)
    cast_parser.add_argument('--name', required=False)
    
    # Dig subcommand  
    dig_parser = subparsers.add_parser('dig')
    dig_parser.add_argument('--query', required=True)
    
    # etc...
    
    return parser.parse_args(args)
```

### 4. Backward Compatibility
**Decision Required:** How to handle old syntax during transition?

**Options:**
1. **Hard Break:** Immediately reject old syntax with error message
2. **Graceful Migration:** Support both syntaxes with deprecation warnings
3. **Alias System:** Auto-convert old → new syntax

**Recommendation:** Start with Option 2 (graceful migration) to avoid breaking existing user workflows.

### 5. Testing Requirements
- Update ALL existing tests to use new `--flag` syntax
- Add tests for argument validation (missing required flags)
- Test error messages for malformed commands
- Verify backward compatibility during transition

### 6. Documentation Updates
- ✅ Command reference updated
- Update help system (`/help` command)
- Update inline help (`--help` flags)
- Update error messages to show correct syntax

## Implementation Priority

1. **High Priority (Week 1):**
   - Update command parser to recognize `--flags`
   - Update `/mine`, `/ask`, `/save` commands
   - Basic testing

2. **Medium Priority (Week 2):**
   - Update remaining commands (`/analyze`, `/summarize`, `/backup`, `/restore`, `/config`)
   - Comprehensive testing
   - Error message updates

3. **Low Priority (Week 3):**
   - Backward compatibility removal (if desired)
   - Performance optimization
   - Advanced validation

## User Experience Impact

**Before:** `/mine dig "query"` (confusing - is "dig" a command or arg?)
**After:** `/mine --dig "query"` (clear - "--dig" is clearly a flag)

**Benefits:**
- ✅ Eliminates ambiguity between commands and arguments
- ✅ Consistent syntax across ALL commands  
- ✅ Easier to read and understand command structure
- ✅ Better autocomplete and help system support

## Risk Assessment

**High Risk:** Command parser changes could break all commands
**Mitigation:** Implement gradual migration with comprehensive testing

**Medium Risk:** User confusion during transition
**Mitigation:** Clear error messages showing new syntax

**Low Risk:** Performance impact
**Mitigation:** argparse is standard library, minimal overhead

## Success Criteria

- [ ] All commands accept `--flag` syntax
- [ ] Old syntax rejected with helpful error messages
- [ ] All existing functionality preserved
- [ ] Comprehensive test coverage
- [ ] Documentation matches implementation
- [ ] User can run: `/mine --dig "test query"` successfully

## Next Steps

1. **Immediate:** Review this handoff and assign implementation team
2. **Day 1:** Begin command parser updates
3. **Day 3:** Update high-priority commands
4. **Day 7:** Complete all command updates
5. **Day 10:** Full testing and user validation

---

**Handoff Created:** October 23, 2025
**Requested By:** User (frustrated with confusing syntax)
**Priority:** Critical - User Experience