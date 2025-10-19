# Implementation: Translator Module

## Goal
Create translator module that converts natural language to shell commands using ClaudeClient.

**Time Estimate:** 30 minutes

---

## File to Create

**Path:** `isaac/ai/translator.py`

**Lines:** ~100

---

## Complete Implementation

```python
"""
Translator - Natural language to shell command conversion
Uses ClaudeClient to translate user queries to executable commands
"""

from typing import Dict
from isaac.ai.claude_client import ClaudeClient


def translate_query(query: str, shell_name: str, session_mgr) -> Dict:
    """
    Translate natural language query to shell command.
    
    Args:
        query: User's natural language query (without "isaac " prefix)
        shell_name: Target shell (bash, PowerShell, etc.)
        session_mgr: SessionManager instance (for config access)
        
    Returns:
        dict: {
            'success': True,
            'query': 'find large files',
            'command': 'find . -type f -size +100M',
            'explanation': 'Finds files larger than 100MB',
            'confidence': 0.95
        }
        
        or error:
        {
            'success': False,
            'error': 'error message'
        }
    """
    # Check if AI enabled
    if not session_mgr.config.get('ai_enabled', False):
        return {
            'success': False,
            'error': 'AI features disabled. Enable in config: ai_enabled: true'
        }
    
    # Get Claude API key
    api_key = session_mgr.config.get('claude_api_key', '')
    if not api_key:
        return {
            'success': False,
            'error': 'Claude API key not configured. Add to ~/.isaac/config.json'
        }
    
    # Initialize Claude client
    try:
        model = session_mgr.config.get('ai_model', 'claude-sonnet-4-5-20250929')
        client = ClaudeClient(api_key=api_key, model=model)
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to initialize AI client: {str(e)}'
        }
    
    # Call Claude API
    result = client.translate_to_shell(query, shell_name)
    
    if not result.get('success'):
        return result  # Return error from ClaudeClient
    
    # Add original query to response
    result['query'] = query
    
    # Validate translation
    command = result.get('command', '')
    if not command or len(command) == 0:
        return {
            'success': False,
            'error': 'AI returned empty command'
        }
    
    # Check confidence threshold
    confidence = result.get('confidence', 0.0)
    min_confidence = session_mgr.config.get('ai_min_confidence', 0.7)
    
    if confidence < min_confidence:
        return {
            'success': False,
            'error': f'Low confidence ({confidence:.2f}). Not safe to execute.'
        }
    
    return result


def is_shell_related_query(query: str) -> bool:
    """
    Check if query is related to shell commands.
    
    Args:
        query: User's natural language query
        
    Returns:
        bool: True if query seems shell-related
    """
    # Simple heuristic: check for shell-related keywords
    shell_keywords = [
        'find', 'search', 'list', 'show', 'create', 'delete', 'remove',
        'copy', 'move', 'rename', 'edit', 'run', 'execute', 'install',
        'backup', 'archive', 'compress', 'extract', 'download', 'upload',
        'file', 'folder', 'directory', 'process', 'service', 'network',
        'disk', 'memory', 'cpu', 'system', 'permission', 'user', 'group'
    ]
    
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in shell_keywords)


def validate_translation_safety(command: str, shell_name: str) -> Dict:
    """
    Quick safety check on translated command.
    
    Args:
        command: Translated shell command
        shell_name: Target shell
        
    Returns:
        dict: {'safe': bool, 'reason': str}
    """
    # Check for obviously dangerous patterns
    dangerous_patterns = [
        'rm -rf /',
        'format c:',
        'del /s /q c:\\',
        'dd if=/dev/zero',
        ':(){ :|:& };:',  # fork bomb
    ]
    
    command_lower = command.lower()
    
    for pattern in dangerous_patterns:
        if pattern in command_lower:
            return {
                'safe': False,
                'reason': f'Command contains dangerous pattern: {pattern}'
            }
    
    return {'safe': True, 'reason': 'No obvious dangerous patterns detected'}
```

---

## Verification Steps

After creating `isaac/ai/translator.py`, verify:

- [ ] File has ~135 lines
- [ ] `translate_query()` function complete
- [ ] Checks for `ai_enabled` config
- [ ] Checks for `claude_api_key` config
- [ ] Validates confidence threshold
- [ ] Returns proper dict format
- [ ] No syntax errors: `python -m py_compile isaac/ai/translator.py`

---

## Integration Points

**Called from:** `isaac/core/command_router.py`

**Usage:**
```python
from isaac.ai.translator import translate_query

result = translate_query(
    query="find large files",
    shell_name="bash",
    session_mgr=self.session
)

if result['success']:
    command = result['command']
    # Route through tier system
    return self.route_command(command)
```

---

## Configuration Requirements

**User config** (`~/.isaac/config.json`):
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-...",
  "ai_model": "claude-sonnet-4-5-20250929",
  "ai_min_confidence": 0.7
}
```

**Defaults if not set:**
- `ai_enabled`: false (AI features off)
- `ai_model`: "claude-sonnet-4-5-20250929"
- `ai_min_confidence`: 0.7 (70% confidence required)

---

## Error Handling

**Scenario 1: AI disabled**
```python
result = translate_query("test", "bash", session)
# Returns: {'success': False, 'error': 'AI features disabled...'}
```

**Scenario 2: No API key**
```python
result = translate_query("test", "bash", session)
# Returns: {'success': False, 'error': 'Claude API key not configured...'}
```

**Scenario 3: API failure**
```python
result = translate_query("test", "bash", session)
# Returns: {'success': False, 'error': 'API timeout (10 seconds)'}
```

**Scenario 4: Low confidence**
```python
result = translate_query("ambiguous query", "bash", session)
# Returns: {'success': False, 'error': 'Low confidence (0.45). Not safe to execute.'}
```

---

## Testing

**Manual test:**
```python
from isaac.ai.translator import translate_query
from isaac.core.session_manager import SessionManager

session = SessionManager()
result = translate_query("find large files", "bash", session)

print(result)
# Expected: {'success': True, 'command': '...', 'confidence': 0.95}
```

---

## Common Pitfalls

⚠️ **Don't bypass tier system:**
```python
# WRONG - executes directly
shell.execute(result['command'])

# CORRECT - goes through tier validation
self.route_command(result['command'])
```

⚠️ **Check success before using result:**
```python
result = translate_query(...)
if result['success']:
    command = result['command']  # Safe
else:
    print(result['error'])  # Handle error
```

⚠️ **Always validate config:**
```python
# Check ai_enabled BEFORE calling ClaudeClient
if not session.config.get('ai_enabled', False):
    return error_dict
```

---

**END OF IMPLEMENTATION**
