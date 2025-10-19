# Implementation: Claude API Client (Continued)

## Part 5: Method 3 - correct_typo()

**Add to claude_client.py:**

```python
    def correct_typo(self, command: str, shell_name: str) -> Dict:
        """
        Detect and correct typos in shell command.
        
        Args:
            command: Potentially misspelled command
            shell_name: Shell context
            
        Returns:
            dict: {
                'corrected': 'grep -r "pattern" .',
                'original': 'grp -r "pattern" .',
                'confidence': 0.9
            }
        """
        prompt = f"""Detect typos in this {shell_name} command.

Command: {command}

Respond in JSON format:
{{
    "has_typo": true,
    "corrected": "corrected command",
    "confidence": 0.9
}}

Common typos:
- grp → grep
- cd /tm → cd /tmp
- eco → echo

If no typo detected, set has_typo to false and corrected to same as original.
Only respond with JSON, no other text."""

        result = self._call_api(prompt, max_tokens=256)
        
        if not result['success']:
            # No correction available
            return {
                'corrected': None,
                'original': command,
                'confidence': 0.0
            }
        
        try:
            parsed = json.loads(result['text'])
            has_typo = parsed.get('has_typo', False)
            
            if has_typo:
                return {
                    'corrected': parsed.get('corrected', command),
                    'original': command,
                    'confidence': parsed.get('confidence', 0.5)
                }
            else:
                return {
                    'corrected': None,
                    'original': command,
                    'confidence': 1.0
                }
        except json.JSONDecodeError:
            return {
                'corrected': None,
                'original': command,
                'confidence': 0.0
            }
```

---

## Part 6: Method 4 - plan_task()

**Add to claude_client.py:**

```python
    def plan_task(self, task_description: str, shell_name: str) -> Dict:
        """
        Break multi-step task into executable steps.
        
        Args:
            task_description: User's task goal
            shell_name: Target shell
            
        Returns:
            dict: {
                'steps': [
                    {'command': 'cd /backup', 'tier': 1, 'description': '...'},
                    {'command': 'tar -czf ...', 'tier': 3, 'description': '...'}
                ],
                'estimated_duration': '2 minutes',
                'risks': ['Large file transfer']
            }
        """
        prompt = f"""Break this task into {shell_name} commands.

Task: {task_description}

Respond in JSON format:
{{
    "steps": [
        {{
            "command": "shell command",
            "tier": 1,
            "description": "what this step does"
        }}
    ],
    "estimated_duration": "time estimate",
    "risks": ["list of risks"]
}}

Tier guidelines:
- Tier 1: Read-only, safe (ls, cd, cat)
- Tier 2: Minor writes (echo, touch)
- Tier 3: Destructive (rm, mv, git push)
- Tier 4: Critical system (dd, format, reboot)

Only respond with JSON, no other text."""

        result = self._call_api(prompt, max_tokens=1024, temperature=0.2)
        
        if not result['success']:
            return {
                'success': False,
                'error': result['error']
            }
        
        try:
            parsed = json.loads(result['text'])
            return {
                'success': True,
                'steps': parsed.get('steps', []),
                'estimated_duration': parsed.get('estimated_duration', 'Unknown'),
                'risks': parsed.get('risks', [])
            }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Failed to parse task plan'
            }
```

---

## Complete File Check

**After implementing all 4 parts, your claude_client.py should have:**
- Class ClaudeClient
- Method __init__()
- Method _call_api() (private helper)
- Method translate_to_shell()
- Method validate_command()
- Method correct_typo()
- Method plan_task()

**Total:** ~200 lines

---

## Verification Steps

After creating the file:

```bash
# 1. Check syntax
python -m py_compile isaac/ai/claude_client.py

# 2. Test imports
python -c "from isaac.ai.claude_client import ClaudeClient; print('✅ Import successful')"

# 3. Basic instantiation (will fail without API key, but checks structure)
python -c "from isaac.ai.claude_client import ClaudeClient; c = ClaudeClient('test-key'); print('✅ Class instantiated')"
```

**Expected Output:**
```
✅ Import successful
✅ Class instantiated
```

---

## Common Pitfalls

⚠️ **Pitfall 1: Missing API Version Header**
- Symptom: 400 Bad Request from Claude API
- Fix: Ensure `anthropic-version` header is set in _call_api()

⚠️ **Pitfall 2: JSON Parsing Fails**
- Symptom: JSONDecodeError
- Fix: All methods catch this and return safe error dict

⚠️ **Pitfall 3: Network Timeouts**
- Symptom: Long waits, no response
- Fix: 10-second timeout already set, returns error dict

⚠️ **Pitfall 4: Invalid API Key**
- Symptom: 401 Unauthorized
- Fix: User must set valid claude_api_key in ~/.isaac/config.json

---

## Testing Without API Key

**For development without Claude API access:**

Create a mock file: `isaac/ai/claude_client_mock.py`

```python
"""Mock ClaudeClient for testing without API access."""
from typing import Dict

class ClaudeClient:
    def __init__(self, api_key: str, model: str = "mock"):
        self.api_key = api_key
        self.model = model
    
    def translate_to_shell(self, natural_language: str, shell_name: str) -> Dict:
        # Mock translation
        if "find" in natural_language.lower():
            return {
                'success': True,
                'command': 'find . -type f',
                'explanation': 'Mock translation',
                'confidence': 0.8
            }
        return {'success': False, 'error': 'Mock: Unknown query'}
    
    # ... add other methods with mock responses
```

**Switch imports during testing:**
```python
# In test code
from isaac.ai.claude_client_mock import ClaudeClient  # Mock version
```

---

**END OF IMPLEMENTATION**
