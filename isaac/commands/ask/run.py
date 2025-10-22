#!/usr/bin/env python3
"""
/ask command - Direct AI chat interface.

Unlike translation mode (isaac <query>), this sends queries directly to AI
and returns text responses without executing commands.
"""
import sys
import json
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.ai.xai_client import XaiClient
from isaac.core.session_manager import SessionManager


def _handle_chat_query(query: str, config: dict, session: SessionManager) -> str:
    """Handle regular chat queries (existing logic)"""
    # Get Chat API configuration - use nested structure
    xai_config = config.get('xai', {})
    chat_config = xai_config.get('chat', {})
    api_key = chat_config.get('api_key')
    
    # Fallback to old flat structure for backward compatibility
    if not api_key:
        api_key = config.get('xai_api_key') or config.get('api_key')
    
    if not api_key:
        raise Exception("xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key")
    
    # Initialize xAI client
    client = XaiClient(
        api_key=api_key,
        api_url=config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
        model=config.get('xai_model', 'grok-3')
    )
    
    # Build chat preprompt (context-aware with history)
    preprompt = _build_chat_preprompt(session, query)
    
    # Query AI
    return client.chat(
        prompt=query,
        system_prompt=preprompt
    )


def main():
    """Main entry point for ask command"""
    try:
        # Check if we're being called through dispatcher (stdin has JSON) or standalone
        if not sys.stdin.isatty():
            # Called through dispatcher - read JSON payload from stdin
            payload = json.loads(sys.stdin.read())
            command = payload.get('command', '')
            
            # Strip the trigger to get the query
            query = ''
            if command.startswith('/ask '):
                query = command[5:].strip()
            elif command.startswith('/a '):
                query = command[3:].strip()
        else:
            # Standalone execution - get query from command line args
            if len(sys.argv) < 2:
                print("Usage: python -m isaac.commands.ask.run <query>")
                print("Or: /ask <query> (within Isaac shell)")
                sys.exit(1)
            query = ' '.join(sys.argv[1:])
        
        if not query:
            if not sys.stdin.isatty():
                # Dispatcher mode - return JSON error
                print(json.dumps({
                    "ok": False,
                    "kind": "text",
                    "stdout": "Error: No query provided. Usage: /ask <question>",
                    "meta": {}
                }))
            else:
                # Standalone mode - print error directly
                print("Error: No query provided. Usage: python -m isaac.commands.ask.run <query>")
            return
        
        # Get session
        session = SessionManager()
        
        # Get API configuration - use nested structure for chat
        config = session.get_config()
        xai_config = config.get('xai', {})
        chat_config = xai_config.get('chat', {})
        api_key = chat_config.get('api_key')
        
        # Fallback to old flat structure for backward compatibility
        if not api_key:
            api_key = config.get('xai_api_key') or config.get('api_key')
        
        if not api_key:
            if not sys.stdin.isatty():
                # Dispatcher mode - return JSON error
                print(json.dumps({
                    "ok": False,
                    "kind": "text",
                    "stdout": "Error: xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key",
                    "meta": {}
                }))
            else:
                # Standalone mode - print error directly
                print("Error: xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key")
            return
        
        # Initialize xAI client
        client = XaiClient(
            api_key=api_key,
            api_url=config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
            model=config.get('xai_model', 'grok-3')
        )
        
        # Handle as chat query (collections logic removed - now chat-only)
        response = _handle_chat_query(query, config, session)
        
        # Log query to AI history
        session.log_ai_query(
            query=query,
            translated_command='[chat_mode]',
            explanation=response[:100],
            executed=False,
            shell_name='chat'
        )
        
        # Return response
        if not sys.stdin.isatty():
            # Dispatcher mode - return JSON
            print(json.dumps({
                "ok": True,
                "kind": "text",
                "stdout": response,
                "meta": {"mode": "chat"}
            }))
        else:
            # Standalone mode - print response directly
            print(response)
    
    except Exception as e:
        if not sys.stdin.isatty():
            # Dispatcher mode - return JSON error
            print(json.dumps({
                "ok": False,
                "kind": "text",
                "stdout": f"Error: {e}",
                "meta": {}
            }))
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


def _build_chat_preprompt(session: SessionManager, current_query: str) -> str:
    """
    Build context-aware preprompt for chat mode with conversation history.
    
    Includes:
    - System context (OS, shell, current directory)
    - User preferences
    - Recent chat history (for memory)
    """
    # Get system context
    shell_name = 'PowerShell'  # Default for Windows
    if hasattr(session, 'shell_adapter') and session.shell_adapter:
        shell_name = session.shell_adapter.__class__.__name__.replace('Adapter', '')
    
    current_dir = Path.cwd()
    
    preprompt = f"""You are Isaac, an AI assistant integrated into the user's shell.

CONTEXT:
- Operating System: Windows
- Current Shell: {shell_name}
- Current Directory: {current_dir}

IMPORTANT DISTINCTIONS:
1. Geographic/General Questions: Answer directly
   - "where is alaska?" → Geographic information
   - "what is docker?" → Technical explanation
   
2. File/Command Questions: Mention the command but don't execute
   - "where is alaska.exe?" → "You can search with: where.exe alaska.exe"
   - "show me my files" → "You can list files with: ls or dir"

3. Shell-Specific Awareness:
   - User is on {shell_name}, so reference appropriate commands
   - PowerShell: Get-*, Set-*, cmdlets
   - Bash: ls, grep, awk, sed

RESPONSE STYLE:
- Conversational and helpful
- Brief but complete answers
- Reference shell commands when relevant
- No command execution (this is chat mode)
"""
    
    # Add conversation history if available
    try:
        if hasattr(session, 'ai_query_history') and session.ai_query_history:
            recent_queries = session.ai_query_history.get_recent(count=5)
            
            # Filter to only chat mode queries (not translation mode)
            chat_queries = [
                q for q in recent_queries 
                if q.get('shell') == 'chat' or q.get('command') == '[chat_mode]'
            ]
            
            if chat_queries:
                preprompt += "\n\nRECENT CONVERSATION HISTORY:\n"
                preprompt += "(Use this to maintain context and answer questions about previous exchanges)\n\n"
                
                for i, q in enumerate(reversed(chat_queries), 1):  # Chronological order
                    query_text = q.get('query', '')
                    response_preview = q.get('explanation', '')[:100]  # First 100 chars of response
                    
                    preprompt += f"{i}. User asked: \"{query_text}\"\n"
                    if response_preview:
                        preprompt += f"   You responded: \"{response_preview}...\"\n"
                    preprompt += "\n"
                
                preprompt += "You can reference these previous exchanges when relevant.\n"
    except Exception as e:
        # Don't fail if history unavailable, just skip it
        pass
    
    preprompt += "\nCurrent user query follows below:\n"
    
    return preprompt


if __name__ == "__main__":
    main()
