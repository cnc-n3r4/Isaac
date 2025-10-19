# Implementation: Claude API Client

## Goal
Create ClaudeClient class with 4 AI methods for Isaac intelligence.

**Time Estimate:** 2 hours

---

## Files to Create

**1. isaac/ai/__init__.py**
```python
"""AI integration module for Isaac."""
```

**2. isaac/ai/claude_client.py** (~200 lines, will break into chunks)

---

## Part 1: Imports and Class Structure

**File:** `isaac/ai/claude_client.py`

```python
"""
ClaudeClient - HTTP wrapper for Claude AI API
Enables natural language translation, validation, correction, and task planning
"""

import requests
import json
from typing import Dict, List, Optional


class ClaudeClient:
    """HTTP client for Claude AI API integration."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Claude API client.
        
        Args:
            api_key: Anthropic API key (sk-ant-...)
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.timeout = 10  # 10-second timeout
        self.api_version = "2023-06-01"
```

---

## Part 2: Helper Method _call_api()

**Add to claude_client.py:**

```python
    def _call_api(self, prompt: str, max_tokens: int = 1024, temperature: float = 0) -> Dict:
        """
        Internal method to call Claude API.
        
        Args:
            prompt: User prompt for Claude
            max_tokens: Maximum response tokens
            temperature: Creativity (0 = deterministic)
            
        Returns:
            dict: Response data or error dict
        """
        try:
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': self.api_version,
                'content-type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract text from response
                text = data['content'][0]['text']
                return {'success': True, 'text': text}
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': 'API timeout (10 seconds)'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Network connection failed'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
```

---

## Part 3: Method 1 - translate_to_shell()

**Add to claude_client.py:**


```python
    def translate_to_shell(self, natural_language: str, shell_name: str) -> Dict:
        """
        Translate natural language query to shell command.
        
        Args:
            natural_language: User's query (e.g., "find large files")
            shell_name: Target shell (PowerShell, bash, etc.)
            
        Returns:
            dict: {
                'success': True,
                'command': 'find . -type f -size +100M',
                'explanation': 'Finds files larger than 100MB',
                'confidence': 0.95
            }
        """
        prompt = f"""Translate this natural language query to a {shell_name} command.

Query: {natural_language}

Respond in JSON format:
{{
    "command": "the shell command",
    "explanation": "brief explanation of what it does",
    "confidence": 0.95
}}

Only respond with the JSON, no other text."""

        result = self._call_api(prompt, max_tokens=512)
        
        if not result['success']:
            return result  # Return error dict
        
        try:
            # Parse JSON from Claude's response
            parsed = json.loads(result['text'])
            return {
                'success': True,
                'command': parsed.get('command', ''),
                'explanation': parsed.get('explanation', ''),
                'confidence': parsed.get('confidence', 0.5)
            }
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Failed to parse AI response'
            }
```

---

## Part 4: Method 2 - validate_command()

**Add to claude_client.py:**

```python
    def validate_command(self, command: str, shell_name: str) -> Dict:
        """
        Validate shell command for safety and correctness.
        
        Args:
            command: Shell command to validate
            shell_name: Shell context
            
        Returns:
            dict: {
                'safe': True,
                'warnings': ['Will delete 500 files'],
                'suggestions': ['Add -i flag']
            }
        """
        prompt = f"""Analyze this {shell_name} command for safety.

Command: {command}

Respond in JSON format:
{{
    "safe": true,
    "warnings": ["list of warnings"],
    "suggestions": ["list of suggestions"]
}}

Consider:
- Data loss risks
- System impact
- Best practices

Only respond with JSON, no other text."""

        result = self._call_api(prompt, max_tokens=512)
        
        if not result['success']:
            # Fallback to safe validation
            return {
                'safe': False,
                'warnings': ['AI validation unavailable'],
                'suggestions': ['Proceed with caution']
            }
        
        try:
            parsed = json.loads(result['text'])
            return {
                'safe': parsed.get('safe', False),
                'warnings': parsed.get('warnings', []),
                'suggestions': parsed.get('suggestions', [])
            }
        except json.JSONDecodeError:
            return {
                'safe': False,
                'warnings': ['AI validation failed'],
                'suggestions': []
            }
```

---

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
        prompt = f"""Detect typos in this {shell_name} command and suggest correction.

Command: {command}

Respond in JSON format:
{{
    "has_typo": true,
    "corrected": "corrected command",
    "confidence": 0.9
}}

If no typo detected:
{{
    "has_typo": false,
    "corrected": "{command}",
    "confidence": 1.0
}}

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
            return {
                'corrected': parsed.get('corrected') if parsed.get('has_typo') else None,
                'original': command,
                'confidence': parsed.get('confidence', 0.0)
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
                    {'command': 'cd /backup', 'tier': 1, 'description': 'Navigate'},
                    {'command': 'tar -czf ...', 'tier': 3, 'description': 'Create archive'}
                ],
                'estimated_duration': '2 minutes',
                'risks': ['Large file transfer']
            }
        """
        prompt = f"""Break down this task into {shell_name} commands.

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
    "estimated_duration": "X minutes",
    "risks": ["list of risks"]
}}

Tier guide:
- Tier 1: Safe reads (ls, cat, pwd)
- Tier 2: Safe writes (echo, touch)
- Tier 3: Risky operations (rm, git push)
- Tier 4: Destructive (rm -rf, format)

Only respond with JSON, no other text."""

        result = self._call_api(prompt, max_tokens=1024)
        
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

## Verification Steps

After creating `isaac/ai/claude_client.py`, verify:

- [ ] File has ~230 lines
- [ ] All 4 methods present (translate, validate, correct, plan)
- [ ] No syntax errors: `python -m py_compile isaac/ai/claude_client.py`
- [ ] All methods return dicts (never raise exceptions)
- [ ] Timeout set to 10 seconds
- [ ] JSON parsing wrapped in try/except

---

## Test Manually (Optional)

Create test script `test_claude.py`:

```python
from isaac.ai.claude_client import ClaudeClient

# Initialize with your API key
client = ClaudeClient(api_key="sk-ant-YOUR_KEY_HERE")

# Test translation
result = client.translate_to_shell("find large files", "bash")
print("Translation:", result)

# Test validation
result = client.validate_command("rm -rf /", "bash")
print("Validation:", result)

# Test correction
result = client.correct_typo("grp pattern file.txt", "bash")
print("Correction:", result)

# Test task planning
result = client.plan_task("backup my project folder", "bash")
print("Task Plan:", result)
```

**Expected:**
- All methods return dicts
- Network errors handled gracefully
- No exceptions raised

---

## Common Pitfalls

⚠️ **API Key Issues:**
- Must start with `sk-ant-`
- Stored in `~/.isaac/config.json` under `claude_api_key`
- If missing: AI features disabled, falls back to MVP behavior

⚠️ **JSON Parsing:**
- Claude sometimes adds explanatory text before/after JSON
- Use try/except around json.loads()
- Return error dict on parse failure

⚠️ **Timeout Handling:**
- 10 seconds is generous but not infinite
- Complex tasks may timeout
- Return error dict, don't raise exception

---

**END OF IMPLEMENTATION**
