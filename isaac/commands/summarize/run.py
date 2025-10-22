"""
Summarize Handler - AI text summarization of piped data
Provides /summarize command for AI-powered summarization of blob content
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
    """Main entry point for summarize command"""
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
                    command = meta.get('command', '/summarize')
                    
                    # Parse command to get summary length
                    summary_length = 'medium'
                    if command.startswith('/summarize '):
                        summary_length = command[11:].strip()
                    
                    # Summarize content
                    result = summarize_content(content, kind, summary_length)
                    
                    # Return blob result
                    print(json.dumps({
                        "kind": "text",
                        "content": result,
                        "meta": {"command": command, "summary_length": summary_length}
                    }))
                else:
                    # This is dispatcher JSON payload
                    payload = blob
                    command = payload.get('command', '')
                    
                    # Strip the trigger to get summary length
                    summary_length = 'medium'
                    if command.startswith('/summarize '):
                        summary_length = command[11:].strip()
                    
                    # For dispatcher mode without piped input, show usage
                    result = f"Usage: <content> | /summarize [{summary_length}]"
                    
                    print(json.dumps({
                        "kind": "text",
                        "content": result,
                        "meta": {"command": command, "summary_length": summary_length}
                    }))
            except json.JSONDecodeError:
                # Not JSON, treat as plain text content to summarize
                content = stdin_data
                summary_length = 'medium'
                
                result = summarize_content(content, 'text', summary_length)
                
                print(json.dumps({
                    "kind": "text",
                    "content": result,
                    "meta": {"command": "/summarize", "summary_length": summary_length}
                }))
        else:
            # Standalone execution - get summary length from command line args
            summary_length = sys.argv[1] if len(sys.argv) > 1 else 'medium'
            
            # For standalone mode, read from stdin if available
            if not sys.stdin.isatty():
                content = sys.stdin.read()
                kind = 'text'
            else:
                print("Usage: <command> | /summarize [short|medium|long]")
                print("Or: echo 'content' | /summarize [short|medium|long] (within Isaac shell)")
                sys.exit(1)
            
            result = summarize_content(content, kind, summary_length)
            print(result)
    
    except Exception as e:
        if not sys.stdin.isatty():
            # Piped/dispatcher mode - return blob error
            print(json.dumps({
                "kind": "error",
                "content": f"Error: {e}",
                "meta": {"command": "/summarize"}
            }))
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


def summarize_content(content: str, kind: str, length: str) -> str:
    """Summarize content using AI."""
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
        
        # Build summarization prompt based on length
        if length == 'short':
            prompt = f"Summarize this {kind} content in 1-2 sentences:\n\n{content[:2000]}"
        elif length == 'long':
            prompt = f"Provide a detailed summary of this {kind} content with key points and main themes:\n\n{content[:4000]}"
        else:  # medium
            prompt = f"Summarize this {kind} content in 3-4 sentences, capturing the main points:\n\n{content[:3000]}"
        
        # Get AI summary
        response = client.chat(
            prompt=prompt,
            system_prompt="You are an AI assistant specialized in creating clear, concise summaries. Focus on the most important information and maintain the original meaning."
        )
        
        # Log query to AI history
        session.log_ai_query(
            query=f"[summary:{length}] {content[:100]}...",
            translated_command=f'/summarize {length}',
            explanation=response[:100],
            executed=True,
            shell_name='summary'
        )
        
        return response
    
    except Exception as e:
        return f"Error summarizing content: {e}"


if __name__ == "__main__":
    main()