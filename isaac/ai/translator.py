"""
Translator - Natural language to shell command conversion
Uses AIRouter for multi-provider translation with fallback
"""

from typing import Dict
from isaac.ai import AIRouter


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
    
    # Get xAI API key
    api_key = session_mgr.config.get('xai_api_key', '')
    if not api_key:
        return {
            'success': False,
            'error': 'xAI API key not configured. Add to ~/.isaac/config.json'
        }
    
    # Initialize AI router with session manager
    try:
        router = AIRouter(session_mgr=session_mgr)
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to initialize AI router: {str(e)}'
        }
    
    # Create translation prompt
    prompt = f"""Translate this natural language query to a {shell_name} command.

Query: {query}

Respond in JSON format:
{{
    "command": "the shell command",
    "explanation": "brief explanation of what it does",
    "confidence": 0.95
}}

Only respond with the JSON, no other text."""
    
    # Prepare messages for router
    messages = [
        {"role": "user", "content": prompt}
    ]
    
    # Call AI router
    response = router.chat(messages=messages, max_tokens=512)
    
    if not response.success:
        return {
            'success': False,
            'error': f'AI translation failed: {response.error}'
        }
    
    try:
        # Parse JSON from AI response
        import json
        parsed = json.loads(response.content)
        result = {
            'success': True,
            'command': parsed.get('command', ''),
            'explanation': parsed.get('explanation', ''),
            'confidence': parsed.get('confidence', 0.5)
        }
    except json.JSONDecodeError:
        return {
            'success': False,
            'error': 'Failed to parse AI response as JSON'
        }
    
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