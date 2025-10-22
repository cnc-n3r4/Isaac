"""
XaiClient - HTTP wrapper for x.ai/Grok AI API
Enables natural language translation, validation, correction, and task planning
"""

import requests
import json
from typing import Dict, List, Optional


class XaiClient:
    """HTTP client for x.ai/Grok API integration."""
    
    def __init__(self, api_key: str, model: str = "grok-3", 
                 api_url: Optional[str] = None, api_version: Optional[str] = None, timeout: Optional[int] = None,
                 provider: Optional[str] = None):
        """
        Initialize x.ai/Grok API client.
        
        Args:
            api_key: x.ai API key
            model: Model to use (default: grok-3)
            api_url: API endpoint URL (default: x.ai official)
            api_version: API version header (not used for x.ai)
            timeout: Request timeout in seconds (default: 10)
            provider: API provider type ('xai', 'openai', 'custom') - auto-detected if not set
        """
        self.api_key = api_key
        self.model = model
        self.api_url = api_url or "https://api.x.ai/v1/chat/completions"
        self.timeout = timeout or 10
        self.api_version = api_version or "2023-06-01"
        
        # Auto-detect provider if not specified
        if provider:
            self.provider = provider.lower()
        else:
            self.provider = 'xai'  # Default to x.ai
    
    def _call_api(self, prompt: str, max_tokens: int = 1024, temperature: float = 0) -> Dict:
        """
        Internal method to call x.ai/Grok API (supports x.ai and OpenAI-compatible APIs).
        
        Args:
            prompt: User prompt
            max_tokens: Maximum response tokens
            temperature: Creativity (0 = deterministic)
            
        Returns:
            dict: Response data or error dict
        """
        return self._call_api_with_messages([{'role': 'user', 'content': prompt}], max_tokens, temperature)

    def _call_api_with_system_prompt(self, system_prompt: str, user_prompt: str, max_tokens: int = 1024, temperature: float = 0) -> Dict:
        """
        Call AI API with separate system and user prompts.
        
        Args:
            system_prompt: System/instruction prompt
            user_prompt: User query
            max_tokens: Maximum response tokens
            temperature: Creativity (0 = deterministic)
            
        Returns:
            dict: Response data or error dict
        """
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ]
        return self._call_api_with_messages(messages, max_tokens, temperature)

    def _call_api_with_messages(self, messages: list, max_tokens: int = 1024, temperature: float = 0) -> Dict:
        """
        Internal method to call x.ai API with custom messages.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum response tokens
            temperature: Creativity (0 = deterministic)
            
        Returns:
            dict: Response data or error dict
        """
        try:
            # Build headers for x.ai API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'content-type': 'application/json'
            }
            
            # x.ai uses OpenAI-compatible format
            payload = {
                'model': self.model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'messages': messages
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse x.ai response (OpenAI-compatible format)
                if 'choices' in data and data['choices']:
                    text = data['choices'][0]['message']['content']
                else:
                    return {'success': False, 'error': 'Invalid response format'}
                
                return {'success': True, 'text': text}
            
            else:
                return {'success': False, 'error': f'API error {response.status_code}: {response.text}'}
                
        except requests.exceptions.Timeout:
            return {'success': False, 'error': f'API timeout ({self.timeout} seconds)'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'Network connection failed'}
        except (KeyError, IndexError) as e:
            return {'success': False, 'error': f'Response parsing error: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'Unexpected error: {str(e)}'}
    
    def chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Direct chat with AI (no command translation).
        
        Args:
            prompt: User query
            system_prompt: Optional system context
        
        Returns:
            AI response text
        
        Raises:
            Exception: If API call fails
        """
        if system_prompt:
            result = self._call_api_with_system_prompt(
                system_prompt=system_prompt,
                user_prompt=prompt,
                max_tokens=1024,
                temperature=0.7
            )
        else:
            result = self._call_api(
                prompt=prompt,
                max_tokens=1024,
                temperature=0.7
            )
        
        if not result['success']:
            raise Exception(result.get('error', 'Unknown API error'))
        
        return result['text']
    
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
            # Parse JSON from x.ai response
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
    
    def validate_command(self, command: str, shell_name: str = "bash") -> Dict:
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
    
    def correct_typo(self, command: str, shell_name: str = "bash") -> Dict:
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
    
    def plan_task(self, task_description: str, shell_name: str = "bash") -> Dict:
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