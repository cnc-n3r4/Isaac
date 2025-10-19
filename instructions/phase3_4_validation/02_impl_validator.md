# Implementation: Validator Module

## Goal
Create validator.py with validate_command() function that calls ClaudeClient.

**Time Estimate:** 30 minutes

---

## File to Create

**Path:** `isaac/ai/validator.py`

**Lines:** ~80

---

## Complete Implementation

```python
"""
Validator - AI-powered command safety validation
Uses ClaudeClient to analyze Tier 3 commands for risks
"""

from typing import Dict
from isaac.ai.claude_client import ClaudeClient


def validate_command(command: str, shell_name: str, config: Dict = None) -> Dict:
    """
    Validate shell command for safety using AI.
    
    Args:
        command: Shell command to validate
        shell_name: Shell context (bash, PowerShell, etc.)
        config: Config dict (optional, for AI settings)
        
    Returns:
        dict: {
            'safe': True/False,
            'warnings': ['list of warnings'],
            'suggestions': ['list of suggestions']
        }
    """
    # Default config if not provided
    if config is None:
        config = {}
    
    # Check if AI validation enabled
    if not config.get('ai_enabled', False):
        return {
            'safe': True,
            'warnings': ['AI validation unavailable'],
            'suggestions': []
        }
    
    # Check if API key exists
    api_key = config.get('claude_api_key', '')
    if not api_key:
        return {
            'safe': True,
            'warnings': ['AI validation unavailable (missing API key)'],
            'suggestions': []
        }
    
    # Initialize Claude client
    try:
        model = config.get('ai_model', 'claude-sonnet-4-5-20250929')
        client = ClaudeClient(api_key, model=model)
    except Exception:
        return {
            'safe': True,
            'warnings': ['AI validation unavailable (initialization failed)'],
            'suggestions': []
        }
    
    # Call Claude API for validation
    try:
        result = client.validate_command(command, shell_name)
        
        return {
            'safe': result.get('safe', False),
            'warnings': result.get('warnings', []),
            'suggestions': result.get('suggestions', [])
        }
    except Exception:
        # Error during validation - fall back to safe defaults
        return {
            'safe': True,
            'warnings': ['AI validation failed (network error)'],
            'suggestions': []
        }
```

---

## Verification Steps

After implementation:

```bash
# 1. Check syntax
python -m py_compile isaac/ai/validator.py

# 2. Test import
python -c "from isaac.ai.validator import validate_command; print('✅ Import successful')"
```

**Expected Output:**
```
✅ Import successful
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Blocking execution**
- Symptom: Commands don't execute even when user confirms
- Fix: Validation is advisory only, always return safe defaults on error

⚠️ **Pitfall 2: Raising exceptions**
- Symptom: Isaac crashes on API errors
- Fix: Wrap all API calls in try/except

⚠️ **Pitfall 3: Empty warnings**
- Symptom: No feedback when AI unavailable
- Fix: Always include at least one warning explaining status

⚠️ **Pitfall 4: Not checking AI enabled**
- Symptom: Errors when AI disabled
- Fix: Check config.get('ai_enabled') first

---

## Testing

**Test 1: With API key**
```python
from isaac.ai.validator import validate_command

config = {
    'ai_enabled': True,
    'claude_api_key': 'sk-ant-...',
    'ai_model': 'claude-sonnet-4-5-20250929'
}

result = validate_command('rm -rf /', 'bash', config)
print(f"Safe: {result['safe']}")
print(f"Warnings: {result['warnings']}")
print(f"Suggestions: {result['suggestions']}")
```

**Expected:**
```
Safe: False
Warnings: ['Will delete entire filesystem', 'Catastrophic data loss', ...]
Suggestions: ['Never run this command', 'Use rm with specific paths', ...]
```

**Test 2: AI disabled**
```python
config = {'ai_enabled': False}
result = validate_command('rm test.txt', 'bash', config)
print(f"Warnings: {result['warnings']}")
```

**Expected:**
```
Warnings: ['AI validation unavailable']
```

**Test 3: Safe command**
```python
result = validate_command('ls -la', 'bash', config)
print(f"Safe: {result['safe']}")
```

**Expected:**
```
Safe: True
```

---

**END OF IMPLEMENTATION**
