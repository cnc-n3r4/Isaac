# Implementation: Corrector Module

## Goal
Create corrector.py with correct_command() function that calls ClaudeClient and handles typos.

**Time Estimate:** 30 minutes

---

## File to Create

**Path:** `isaac/ai/corrector.py`

**Lines:** ~80

---

## Complete Implementation

```python
"""
Corrector - Typo detection and correction for shell commands
Uses ClaudeClient to detect and fix common typos
"""

from typing import Dict
from isaac.ai.claude_client import ClaudeClient


def correct_command(command: str, shell_name: str, config: Dict = None) -> Dict:
    """
    Detect and correct typos in shell command.
    
    Args:
        command: Shell command to check
        shell_name: Shell context (bash, PowerShell, etc.)
        config: Config dict (optional, for AI settings)
        
    Returns:
        dict: {
            'corrected': 'grep pattern file.txt' or None,
            'original': 'grp pattern file.txt',
            'confidence': 0.95
        }
    """
    # Default config if not provided
    if config is None:
        config = {}
    
    # Check if AI correction enabled
    if not config.get('ai_enabled', False) or not config.get('auto_correct_tier2', True):
        return {
            'corrected': None,
            'original': command,
            'confidence': 1.0
        }
    
    # Check if API key exists
    api_key = config.get('claude_api_key', '')
    if not api_key:
        return {
            'corrected': None,
            'original': command,
            'confidence': 1.0
        }
    
    # Initialize Claude client
    try:
        model = config.get('ai_model', 'claude-sonnet-4-5-20250929')
        client = ClaudeClient(api_key, model=model)
    except Exception:
        return {
            'corrected': None,
            'original': command,
            'confidence': 1.0
        }
    
    # Call Claude API
    try:
        result = client.correct_typo(command, shell_name)
        
        # Check if correction found
        if result.get('corrected'):
            return {
                'corrected': result['corrected'],
                'original': command,
                'confidence': result.get('confidence', 0.5)
            }
        else:
            # No typo detected
            return {
                'corrected': None,
                'original': command,
                'confidence': 1.0
            }
    except Exception:
        # Error during correction - fall back to no correction
        return {
            'corrected': None,
            'original': command,
            'confidence': 1.0
        }
```

---

## Verification Steps

After implementation:

```bash
# 1. Check syntax
python -m py_compile isaac/ai/corrector.py

# 2. Test import
python -c "from isaac.ai.corrector import correct_command; print('✅ Import successful')"
```

**Expected Output:**
```
✅ Import successful
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Not checking AI enabled**
- Symptom: Errors when AI disabled
- Fix: Check config.get('ai_enabled') first

⚠️ **Pitfall 2: Correcting when not needed**
- Symptom: Commands slow due to unnecessary API calls
- Fix: Check auto_correct_tier2 setting

⚠️ **Pitfall 3: Raising exceptions**
- Symptom: Isaac crashes on API errors
- Fix: Wrap all API calls in try/except, return no-correction dict

⚠️ **Pitfall 4: Ignoring confidence**
- Symptom: Low confidence corrections applied
- Fix: Caller checks confidence threshold (not corrector's job)

---

## Testing

**Test 1: With API key**
```python
from isaac.ai.corrector import correct_command

config = {
    'ai_enabled': True,
    'auto_correct_tier2': True,
    'claude_api_key': 'sk-ant-...',
    'ai_model': 'claude-sonnet-4-5-20250929'
}

result = correct_command('grp pattern file.txt', 'bash', config)
print(f"Corrected: {result['corrected']}")
print(f"Confidence: {result['confidence']}")
```

**Expected:**
```
Corrected: grep pattern file.txt
Confidence: 0.95
```

**Test 2: AI disabled**
```python
config = {'ai_enabled': False}
result = correct_command('grp pattern file.txt', 'bash', config)
print(f"Corrected: {result['corrected']}")  # Should be None
```

**Test 3: No typo**
```python
result = correct_command('ls -la', 'bash', config)
print(f"Corrected: {result['corrected']}")  # Should be None
print(f"Confidence: {result['confidence']}")  # Should be 1.0
```

---

**END OF IMPLEMENTATION**
