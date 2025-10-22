"""
Corrector - Typo detection and correction for shell commands
Uses ClaudeClient to detect and fix common typos
"""

from typing import Dict, Optional
from isaac.ai.xai_client import XaiClient


def detect_typo(command: str) -> Dict:
    """
    Detect if command contains typos (simplified version).
    
    Args:
        command: Command to check
        
    Returns:
        dict: {'has_typo': bool}
    """
    # Simple heuristic - check for common typos
    common_typos = {
        'grp': 'grep',
        'gerp': 'grep', 
        'lsit': 'list',
        'cd..': 'cd ..'
    }
    
    first_word = command.split()[0] if command.split() else ''
    
    return {
        'has_typo': first_word in common_typos
    }


def correct_command(command: str, shell_name: str = "bash", config: Optional[Dict] = None) -> Dict:
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
    
    # Initialize xAI client
    try:
        model = config.get('ai_model', 'grok-3')
        api_url = config.get('xai_api_url')
        timeout = config.get('xai_timeout')
        client = XaiClient(
            api_key=api_key, 
            model=model,
            api_url=api_url,
            timeout=timeout
        )
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