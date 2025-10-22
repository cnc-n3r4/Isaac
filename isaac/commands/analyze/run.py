"""
Analyze Handler - AI analysis of piped data
Provides /analyze command for AI-powered analysis of blob content
"""

import os
import json
import sys
from typing import Optional

try:
    from isaac.ai.xai_client import XaiClient
    HAS_XAI_CLIENT = True
except ImportError:
    HAS_XAI_CLIENT = False


def main():
    """Main entry point for analyze command"""
    try:
        # Check if we're being called through dispatcher (stdin has JSON) or standalone
        if not sys.stdin.isatty():
            # Called through dispatcher - read JSON payload from stdin
            stdin_data = sys.stdin.read()
            
            # Try to parse as blob format first (for piping)
            try:
                blob = json.loads(stdin_data)
                if isinstance(blob, dict) and 'kind' in blob:
                    # This is piped input in blob format
                    content = blob.get('content', '')
                    kind = blob.get('kind', 'text')
                    meta = blob.get('meta', {})
                    
                    # Extract command from blob meta if available
                    command = meta.get('command', '/analyze')
                    
                    # Parse command to get analysis type
                    analysis_type = 'general'
                    if command.startswith('/analyze '):
                        analysis_type = command[9:].strip()
                    
                    # Analyze content
                    result = analyze_content(content, kind, analysis_type)
                    
                    # Return blob result
                    print(json.dumps({
                        "kind": "text",
                        "content": result,
                        "meta": {"command": command, "analysis_type": analysis_type}
                    }))
                else:
                    # This is dispatcher JSON payload
                    payload = blob
                    command = payload.get('command', '')
                    
                    # Strip the trigger to get analysis type
                    analysis_type = 'general'
                    if command.startswith('/analyze '):
                        analysis_type = command[9:].strip()
                    
                    # For dispatcher mode without piped input, show usage
                    result = f"Usage: <content> | /analyze [{analysis_type}]"
                    
                    print(json.dumps({
                        "kind": "text",
                        "content": result,
                        "meta": {"command": command, "analysis_type": analysis_type}
                    }))
            except json.JSONDecodeError:
                # Not JSON, treat as plain text content to analyze
                content = stdin_data
                analysis_type = 'general'
                
                result = analyze_content(content, 'text', analysis_type)
                
                print(json.dumps({
                    "kind": "text",
                    "content": result,
                    "meta": {"command": "/analyze", "analysis_type": analysis_type}
                }))
        else:
            # Standalone execution - get analysis type from command line args
            analysis_type = sys.argv[1] if len(sys.argv) > 1 else 'general'
            
            # For standalone mode, read from stdin if available
            if not sys.stdin.isatty():
                content = sys.stdin.read()
                kind = 'text'
            else:
                print("Usage: <command> | /analyze [analysis_type]")
                print("Or: echo 'content' | /analyze [analysis_type] (within Isaac shell)")
                sys.exit(1)
            
            result = analyze_content(content, kind, analysis_type)
            print(result)
    
    except Exception as e:
        if not sys.stdin.isatty():
            # Piped/dispatcher mode - return blob error
            print(json.dumps({
                "kind": "error",
                "content": f"Error: {e}",
                "meta": {"command": "/analyze"}
            }))
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


def analyze_content(content: str, kind: str, analysis_type: str) -> str:
    """Analyze content using AI."""
    if not HAS_XAI_CLIENT:
        return "Error: xAI client not available. Check xai_sdk installation and API key configuration."
    
    try:
        # Get session for configuration
        from isaac.core.session_manager import SessionManager
        session = SessionManager()
        config = session.get_config()
        
        # Get API configuration
        xai_config = config.get('xai', {})
        chat_config = xai_config.get('chat', {})
        api_key = chat_config.get('api_key')
        
        # Fallback to old flat structure
        if not api_key:
            api_key = config.get('xai_api_key') or config.get('api_key')
        
        if not api_key:
            return "Error: xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key"
        
        # Initialize xAI client
        client = XaiClient(
            api_key=api_key,
            api_url=config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
            model=config.get('xai_model', 'grok-3')
        )
        
        # Build analysis prompt based on type and content kind
        if analysis_type == 'sentiment':
            prompt = f"Analyze the sentiment of this {kind} content. Provide a sentiment score (-1 to 1) and brief explanation:\n\n{content[:2000]}"
        elif analysis_type == 'summary':
            prompt = f"Summarize this {kind} content in 2-3 sentences:\n\n{content[:2000]}"
        elif analysis_type == 'keywords':
            prompt = f"Extract the main keywords and key phrases from this {kind} content:\n\n{content[:2000]}"
        elif analysis_type == 'code':
            prompt = f"Analyze this code for potential issues, improvements, and best practices:\n\n{content[:2000]}"
        elif analysis_type == 'data':
            prompt = f"Analyze this data structure and provide insights about its content and structure:\n\n{content[:2000]}"
        else:
            prompt = f"Provide a general analysis of this {kind} content, including main themes, key points, and insights:\n\n{content[:2000]}"
        
        # Get AI analysis
        response = client.chat(
            prompt=prompt,
            system_prompt="You are an AI assistant specialized in content analysis. Provide clear, concise, and accurate analysis."
        )
        
        # Log query to AI history
        session.log_ai_query(
            query=f"[analysis:{analysis_type}] {content[:100]}...",
            translated_command=f'/analyze {analysis_type}',
            explanation=response[:100],
            executed=True,
            shell_name='analysis'
        )
        
        return response
    
    except Exception as e:
        return f"Error analyzing content: {e}"


if __name__ == "__main__":
    main()