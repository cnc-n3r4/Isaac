"""
AI Command Validation Module for Isaac

Provides intelligent command safety validation using x.ai/Grok AI.
Returns warnings and suggestions for potentially dangerous commands.
"""

import logging
from typing import Dict, List, Any
from isaac.ai.xai_client import XaiClient

logger = logging.getLogger(__name__)


def validate_command(command: str, shell_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a command for safety using AI analysis.

    Args:
        command: The shell command to validate
        shell_type: 'bash' or 'powershell'
        config: Configuration dict with AI settings

    Returns:
        Dict with keys:
        - safe: bool - Whether command appears safe
        - warnings: List[str] - Safety concerns found
        - suggestions: List[str] - Improvement suggestions
        - error: str - Error message if validation failed
    """
    # Check if AI is enabled
    if not config.get('ai_enabled', False):
        return {
            'safe': True,  # Default to safe when AI disabled
            'warnings': ['AI validation unavailable'],
            'suggestions': [],
            'error': None
        }

    try:
        # Initialize x.ai client
        api_key = config.get('xai_api_key', '')
        model = config.get('ai_model', 'grok-beta')
        api_url = config.get('xai_api_url')
        api_version = config.get('xai_api_version')
        timeout = config.get('xai_timeout')
        provider = config.get('ai_provider')
        xai_client = XaiClient(
            api_key, 
            model,
            api_url=api_url,
            api_version=api_version,
            timeout=timeout,
            provider=provider
        )

        # Call validation API
        result = xai_client.validate_command(command, shell_type)

        # Handle API errors
        if 'error' in result:
            logger.warning(f"AI validation failed: {result['error']}")
            return {
                'safe': True,  # Default to safe on error
                'warnings': [f'AI validation failed: {result["error"]}'],
                'suggestions': [],
                'error': result['error']
            }

        # Return successful validation
        return {
            'safe': result.get('safe', True),
            'warnings': result.get('warnings', []),
            'suggestions': result.get('suggestions', []),
            'error': None
        }

    except Exception as e:
        logger.error(f"Unexpected error in validate_command: {e}")
        return {
            'safe': True,  # Default to safe on exception
            'warnings': [f'Validation error: {str(e)}'],
            'suggestions': [],
            'error': str(e)
        }