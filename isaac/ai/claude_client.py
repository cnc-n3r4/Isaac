"""
ClaudeClient - HTTP wrapper for Claude AI API
Enables natural language translation, validation, correction, and task planning
"""

import requests
import json
from typing import Dict, List, Optional


class ClaudeClient:
    """HTTP client for AI API integration (Claude, OpenAI, or compatible APIs)."""
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929", 
                 api_url: str = None, api_version: str = None, timeout: int = None,
                 provider: str = None):
        """
        Initialize AI API client.
        
        Args:
            api_key: API key (Anthropic, OpenAI, etc.)
            model: Model to use
            api_url: API endpoint URL (default: Anthropic official)
            api_version: API version header (only for Claude/Anthropic)
            timeout: Request timeout in seconds (default: 10)
            provider: API provider type ('claude', 'openai', 'custom') - auto-detected if not set
        """
        self.api_key = api_key
        self.model = model
        self.api_url = api_url or "https://api.anthropic.com/v1/messages"
        self.timeout = timeout or 10
        self.api_version = api_version or "2023-06-01"
        
        # Auto-detect provider if not specified
        if provider:
            self.provider = provider.lower()
        elif 'anthropic.com' in self.api_url or 'claude' in self.model.lower():
            self.provider = 'claude'
        elif 'openai.com' in self.api_url or 'gpt' in self.model.lower():
            self.provider = 'openai'
        else:
            self.provider = 'custom'
    
    def _call_api(self, prompt: str, max_tokens: int = 1024, temperature: float = 0) -> Dict:
        """
        Internal method to call AI API (supports Claude, OpenAI, and compatible APIs).
        
        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens
            temperature: Creativity (0 = deterministic)
            
        Returns:
            dict: Response data or error dict
        """
        try:
            # Build headers based on provider
            if self.provider == 'claude':
                headers = {
                    'x-api-key': self.api_key,
                    'anthropic-version': self.api_version,
                    'content-type': 'application/json'
                }
                payload = {
                    'model': self.model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': [{'role': 'user', 'content': prompt}]
                }
            elif self.provider == 'openai':
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'content-type': 'application/json'
                }
                payload = {
                    'model': self.model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': [{'role': 'user', 'content': prompt}]
                }
            else:  # custom provider - try Claude format first
                headers = {
                    'x-api-key': self.api_key,
                    'Authorization': f'Bearer {self.api_key}',  # Include both
                    'content-type': 'application/json'
                }
                if self.api_version:
                    headers['anthropic-version'] = self.api_version
                payload = {
                    'model': self.model,
                    'max_tokens': max_tokens,
                    'temperature': temperature,
                    'messages': [{'role': 'user', 'content': prompt}]
                }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response based on provider
                text = None
                if self.provider == 'claude' or 'content' in data:
                    # Claude format: data['content'][0]['text']
                    text = data['content'][0]['text']
                elif self.provider == 'openai' or 'choices' in data:
                    # OpenAI format: data['choices'][0]['message']['content']
                    text = data['choices'][0]['message']['content']
                else:
                    # Try both formats
                    if 'content' in data:
                        text = data['content'][0]['text']
                    elif 'choices' in data:
                        text = data['choices'][0]['message']['content']
                    else:
                        return {'success': False, 'error': 'Unknown response format'}
                
                return {'success': True, 'text': text}
            else:
                return {'success': False, 'error': f'API error: {response.status_code}'}
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': f'API timeout ({self.timeout} seconds)'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Network connection failed'}
        except (KeyError, IndexError) as e:
            return {'success': False, 'error': f'Response parsing error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
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