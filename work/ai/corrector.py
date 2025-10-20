"""
Corrector - Typo detection and correction for shell commands
Uses XaiClient to detect and fix common typos
"""

from typing import Dict, Optional
from isaac.ai.xai_client import XaiClient


def correct_command(command: str, shell_name: str, config: Optional[Dict] = None) -> Dict:
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
    api_key = config.get('xai_api_key', '')
    if not api_key:
        return {
            'corrected': None,
            'original': command,
            'confidence': 1.0
        }
    
    # Initialize x.ai client
    try:
        model = config.get('ai_model', 'grok-beta')
        api_url = config.get('xai_api_url')
        api_version = config.get('xai_api_version')
        timeout = config.get('xai_timeout')
        provider = config.get('ai_provider')
        client = XaiClient(
            api_key, 
            model=model,
            api_url=api_url,
            api_version=api_version,
            timeout=timeout,
            provider=provider
        )
    except Exception:
        return {
            'corrected': None,
            'original': command,
            'confidence': 1.0
        }
    
    # Call x.ai API
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