# Feature Brief: Claude API Client (Phase 3.1)

## Objective
Create HTTP client for Claude AI API to enable natural language translation, command validation, typo correction, and task planning.

## Problem Statement

**Current State:**
- Isaac has placeholders for AI features in command_router.py
- No AI integration exists
- Commands require exact shell syntax
- No intelligent assistance

**Issues:**
- Users must know exact command syntax
- Typos cause command failures
- No validation for dangerous commands
- No multi-step task automation

## Solution

Create `ClaudeClient` class that wraps Anthropic's Claude API. This enables:

1. **Natural Language Translation** - "isaac find large files" → `find . -type f -size +100M`
2. **Command Validation** - AI checks Tier 3 commands for safety
3. **Typo Correction** - "grp file.txt" → "grep file.txt"
4. **Task Planning** - "backup project" → multi-step plan

**Example:**
```
User: isaac find files modified today
ClaudeClient.translate_to_shell() calls API
API returns: find . -type f -mtime 0
Command goes through tier system
Tier 1 command executes instantly
```

## Requirements

### Functional Requirements
- [x] ClaudeClient class with 4 AI methods
- [x] translate_to_shell() - Natural language → shell command
- [x] validate_command() - Safety check for Tier 3 commands
- [x] correct_typo() - Typo detection and correction
- [x] plan_task() - Multi-step task breakdown
- [x] 10-second timeout on all API calls
- [x] Error handling (no exceptions raised)

### Configuration Requirements
- [x] Config has claude_api_key (from Anthropic)
- [x] Config has ai_enabled flag (user control)
- [x] Config has ai_model (default: claude-sonnet-4-5-20250929)

## Architecture Context

### Claude API Specification

**Endpoint:** `https://api.anthropic.com/v1/messages`

**Request Format:**
```json
{
  "model": "claude-sonnet-4-5-20250929",
  "max_tokens": 1024,
  "temperature": 0,
  "messages": [
    {
      "role": "user",
      "content": "Translate this to a bash command: find large files"
    }
  ]
}
```

**Headers:**
```http
x-api-key: sk-ant-...
anthropic-version: 2023-06-01
content-type: application/json
```

**Response Format:**
```json
{
  "id": "msg_...",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "find . -type f -size +100M"
    }
  ],
  "model": "claude-sonnet-4-5-20250929",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 15,
    "output_tokens": 10
  }
}
```

## Variables/Data Structures

### User Config (~/.isaac/config.json)
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-...",
  "ai_model": "claude-sonnet-4-5-20250929",
  "auto_correct_tier2": true,
  "task_mode_enabled": true
}
```

### ClaudeClient Return Formats

**translate_to_shell() success:**
```python
{
    'success': True,
    'command': 'find . -type f -size +100M',
    'explanation': 'Finds files larger than 100MB',
    'confidence': 0.95
}
```

**validate_command() success:**
```python
{
    'safe': True,
    'warnings': ['Will delete 500 files'],
    'suggestions': ['Add -i flag for interactive confirmation']
}
```

**correct_typo() success:**
```python
{
    'corrected': 'grep -r "pattern" .',
    'original': 'grp -r "pattern" .',
    'confidence': 0.9
}
```

**plan_task() success:**
```python
{
    'steps': [
        {'command': 'cd /backup', 'tier': 1},
        {'command': 'tar -czf backup.tar.gz /data', 'tier': 3}
    ],
    'estimated_duration': '2 minutes',
    'risks': ['Large file transfer may take time']
}
```

**Error format (all methods):**
```python
{
    'success': False,
    'error': 'Network timeout'
}
```

## Out of Scope

❌ **Not implementing:**
- Local LLM support (cloud-only for MVP)
- Streaming responses (full response only)
- Chat history across sessions
- Fine-tuning or model selection UI
- Cost tracking/billing

## Success Criteria

✅ **Phase 3.1 Complete When:**

1. ClaudeClient class exists with 4 methods
2. translate_to_shell() returns valid commands
3. validate_command() provides safety warnings
4. correct_typo() detects common mistakes
5. plan_task() creates multi-step plans
6. All methods handle errors gracefully
7. No crashes on API failures
8. API calls have 10-second timeout

## Risk Assessment

**Risk Level:** 🟡 MEDIUM

**Potential Issues:**
1. **API costs** - User pays per token
2. **Rate limits** - Anthropic may throttle requests
3. **Incorrect translations** - AI not perfect
4. **Network failures** - API unreachable

**Mitigations:**
- User controls ai_enabled flag
- Error handling prevents crashes
- Tier system validates all AI commands
- Local caching reduces API calls (future)

## Testing Strategy

### Manual Tests
1. Test translation: "isaac find large files"
2. Test validation: "git push -f origin main"
3. Test correction: "grp pattern file.txt"
4. Test planning: "isaac task: backup project"
5. Test offline: Disconnect network, verify no crash

### Automated Tests
- See tests/test_ai_integration.py (38 tests)
- Run: `pytest tests/test_ai_integration.py -v`

---

**Read Next:** `02_impl_claude_client.md`
