# Feature Brief: Natural Language Translation

## Objective
Enable users to speak naturally to Isaac and have queries translated to shell commands.

**Example:** `isaac find large files` → `find . -type f -size +100M`

---

## Problem Statement

**Current State:**
- Isaac only accepts direct shell commands
- User must know exact command syntax
- Natural language queries rejected with "I have a name, use it."

**Issues:**
- Not beginner-friendly
- Requires shell expertise
- Limits accessibility

---

## Solution

Add AI-powered translation that:
1. Detects "isaac [query]" prefix
2. Calls ClaudeClient to translate query to shell command
3. Shows translated command to user
4. Routes through tier system for validation/confirmation
5. Logs AI query separately (privacy-focused)

**Flow:**
```
User: "isaac find large files"
  ↓
Detect "isaac " prefix, extract "find large files"
  ↓
ClaudeClient.translate_to_shell("find large files", "bash")
  ↓
Returns: {'command': 'find . -type f -size +100M', ...}
  ↓
Log to AI query history (separate from commands)
  ↓
Route through tier system: route_command(translated_command)
  ↓
Tier 1 → Execute immediately
Tier 3 → Show validation, ask confirmation
  ↓
Execute and return result
```

---

## Requirements

### Functional Requirements
- [ ] Detect "isaac [query]" pattern
- [ ] Extract query text (remove "isaac " prefix)
- [ ] Call ClaudeClient.translate_to_shell()
- [ ] Handle translation failures gracefully
- [ ] Log AI queries to separate history file
- [ ] Route translated commands through tier validation
- [ ] Show both query and translated command to user

### Privacy Requirements
- [ ] AI query history stored in `aiquery_history.json`
- [ ] File marked as PRIVATE (no sync to debug bots)
- [ ] Separate from command history
- [ ] User can disable AI query logging via config

### Safety Requirements
- [ ] All translated commands go through tier system
- [ ] Tier 3/4 commands require confirmation
- [ ] User sees translated command before execution
- [ ] Option to abort at any confirmation prompt

---

## Technical Details

**Files to Create:**
1. `isaac/ai/translator.py` (~100 lines)
   - Function: `translate_query(query, shell_name, session_mgr)`
   
2. `isaac/models/aiquery_history.py` (~60 lines)
   - Class: `AIQueryHistory`
   - Methods: `add()`, `to_dict()`, `from_dict()`

**Files to Modify:**
1. `isaac/core/command_router.py` (~15 lines)
   - Method: `route_command()`
   - Lines: 46-53 (AI placeholder)
   
2. `isaac/core/session_manager.py` (~10 lines)
   - Add: `self.ai_query_history = AIQueryHistory()`
   - Add: `log_ai_query()` method

---

## Architecture Context

**From command_router.py:**
```python
# Current placeholder (lines 46-53)
if self._is_natural_language(input_text):
    if not input_text.lower().startswith('isaac '):
        return CommandResult(
            success=False,
            output="Isaac > I have a name, use it.",
            exit_code=-1
        )
    # AI integration in Phase 2
    return CommandResult(
        success=False,
        output="Isaac > AI integration coming in Phase 2.",
        exit_code=-1
    )
```

**Will become:**
```python
if self._is_natural_language(input_text):
    if not input_text.lower().startswith('isaac '):
        return CommandResult(
            success=False,
            output="Isaac > I have a name, use it.",
            exit_code=-1
        )
    
    # AI translation (Phase 3.2)
    from isaac.ai.translator import translate_query
    result = translate_query(
        query=input_text[6:].strip(),  # Remove "isaac "
        shell_name=self.shell.name,
        session_mgr=self.session
    )
    
    if result['success']:
        # Log AI query separately (privacy)
        self.session.log_ai_query(result['query'], result['command'])
        
        # Show translation
        print(f"Isaac > Translating: {result['query']}")
        print(f"Isaac > Command: {result['command']}")
        
        # Route through tier system (safety)
        return self.route_command(result['command'])
    else:
        return CommandResult(
            success=False,
            output=f"Isaac > Translation failed: {result['error']}",
            exit_code=-1
        )
```

---

## Data Structures

**AIQueryHistory:**
```python
{
    "queries": [
        {
            "query": "find large files",
            "command": "find . -type f -size +100M",
            "timestamp": "2025-10-19T12:34:56",
            "machine": "DESKTOP-ABC123",
            "shell": "bash",
            "executed": true,
            "result": "success"
        }
    ]
}
```

**Stored in:** `~/.isaac/aiquery_history.json`

---

## Out of Scope

❌ **Not in this phase:**
- Task mode (multi-step) - Phase 3.5
- Auto-correction - Phase 3.3
- Learning from patterns - Phase 3.6
- Context-aware suggestions
- Command history integration (AI queries separate)

---

## Success Criteria

✅ **Phase 3.2 complete when:**
1. "isaac find large files" → translates to valid find command
2. "isaac delete old logs" → translates to rm command, goes through Tier 3 validation
3. Translation failures show error, don't crash Isaac
4. AI queries logged to separate history file
5. AI query history marked as PRIVATE
6. Translated commands respect tier system
7. User can see both query and translated command

---

## Risk Assessment

**Risk:** Incorrect translations could execute dangerous commands  
**Mitigation:** All translations go through tier validation, user confirmation for Tier 3+

**Risk:** AI query logging privacy leak  
**Mitigation:** Separate file, marked PRIVATE, user can disable

**Risk:** Claude API failures  
**Mitigation:** Error handling, fallback message, doesn't crash Isaac

**Risk:** User confusion about tier prompts  
**Mitigation:** Show both original query and translated command

---

## Example Interactions

**Example 1: Safe query (Tier 1)**
```
User: isaac find large files
Isaac > Translating: find large files
Isaac > Command: find . -type f -size +100M
[Executes immediately, Tier 1]
./large_file1.iso
./large_file2.mp4
```

**Example 2: Dangerous query (Tier 3)**
```
User: isaac delete all log files
Isaac > Translating: delete all log files
Isaac > Command: find . -name "*.log" -type f -delete

============================================================
🤖 AI VALIDATION
============================================================
Command: find . -name "*.log" -type f -delete
Safe: ⚠️  Use with caution

⚠️  Warnings:
  - Will permanently delete files
  - No recycle bin recovery

💡 Suggestions:
  - Test with -print first: find . -name "*.log" -type f -print
  - Add confirmation: find . -name "*.log" -type f -ok rm {} \;
============================================================

Validate this command: find . -name "*.log" -type f -delete? [y/N]
```

**Example 3: Translation failure**
```
User: isaac what's the weather
Isaac > Translating: what's the weather
Isaac > Translation failed: Query not related to shell commands
```

---

**END OF FEATURE BRIEF**
