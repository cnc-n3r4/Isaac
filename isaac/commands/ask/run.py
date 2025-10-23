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


def _handle_chat_query(query: str, config: dict, session: SessionManager, is_piped_input: bool = False) -> str:
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
    
    # Smart truncation for large piped content
    # Collections can have huge chunk sizes - prevent token limit issues
    if is_piped_input and len(query) > 10000:  # ~3000 tokens estimated
        # Extract user question and context data
        if "\n\nContext data:\n" in query:
            parts = query.split("\n\nContext data:\n", 1)
            user_question = parts[0]
            context = parts[1]
            
            # Truncate context intelligently
            max_context_chars = 8000  # ~2500 tokens - safe for most models
            if len(context) > max_context_chars:
                # Keep beginning for context, add truncation notice
                context = context[:max_context_chars] + "\n\n... [Context truncated - original content was too large for API limits]"
            
            query = f"{user_question}\n\nContext data:\n{context}"
    
    # Get timeout from config, default to 30 seconds for chat
    timeout_seconds = chat_config.get('timeout_seconds') or config.get('xai_chat_timeout_seconds', 30)
    
    # Initialize xAI client
    client = XaiClient(
        api_key=api_key,
        api_url=config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
        model=config.get('xai_model', 'grok-3'),
        timeout=timeout_seconds
    )
    
    # Build chat preprompt (context-aware with history)
    preprompt = _build_chat_preprompt(session, query, is_piped_input)
    
    # Query AI
    return client.chat(
        prompt=query,
        system_prompt=preprompt
    )


def main():
    """Main entry point for ask command"""
    command = '/ask'  # Default command
    return_blob = False  # Default to envelope format
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
                    input_content = blob.get('content', '')
                    input_kind = blob.get('kind', 'text')
                    
                    # Get the original command which contains the user's question
                    command = blob.get('meta', {}).get('command', '/ask')
                    
                    # Extract user's question from command (after /ask)
                    user_question = ''
                    if ' | /ask ' in command:
                        # Command is like "/mine dig | /ask what..."
                        parts = command.split(' | /ask ')
                        if len(parts) > 1:
                            user_question = parts[1].strip()
                    elif command.startswith('/ask '):
                        user_question = command[5:].strip()
                    
                    # Build query: combine piped data with user's question
                    if user_question:
                        # User asked a specific question about the data
                        query = f"{user_question}\n\nContext data:\n{input_content}"
                    else:
                        # No question, just analyze the data
                        query = f"Analyze this data:\n\n{input_content}"
                    
                    # This is a pipe call - return blob format
                    return_blob = True
                elif isinstance(blob, dict) and 'manifest' in blob:
                    # This is dispatcher payload
                    payload = blob
                    command = payload.get('command', '')
                    
                    # Strip the trigger to get the query
                    query = ''
                    if command.startswith('/ask '):
                        query = command[5:].strip()
                    elif command.startswith('/a '):
                        query = command[3:].strip()
                    
                    # This is a dispatcher call - return envelope format
                    return_blob = False
                else:
                    # Unknown JSON format
                    query = ''
                    command = '/ask'
                    return_blob = True
            except json.JSONDecodeError:
                # Not JSON, treat as plain text input
                query = stdin_data.strip()
                command = '/ask'
                return_blob = True
        else:
            # Standalone execution - get query from command line args
            if len(sys.argv) < 2:
                print("Usage: python -m isaac.commands.ask.run <query>")
                print("Or: /ask <query> (within Isaac shell)")
                sys.exit(1)
            query = ' '.join(sys.argv[1:])
            command = '/ask'
            return_blob = False
        
        if not query:
            if not sys.stdin.isatty():
                # Piped/dispatcher mode - return blob error
                print(json.dumps({
                    "kind": "error",
                    "content": "Error: No query provided. Usage: /ask <question>",
                    "meta": {"command": command}
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
                if return_blob:
                    # Pipe call - return blob error
                    print(json.dumps({
                        "kind": "error",
                        "content": "Error: xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key",
                        "meta": {"command": command}
                    }))
                else:
                    # Dispatcher call - return envelope error
                    print(json.dumps({
                        "ok": False,
                        "error": {
                            "code": "CONFIG_ERROR",
                            "message": "xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key"
                        }
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
        response = _handle_chat_query(query, config, session, is_piped_input=return_blob)
        
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
            if return_blob:
                # Pipe call - return blob
                print(json.dumps({
                    "kind": "text",
                    "content": response,
                    "meta": {"command": command, "mode": "chat"}
                }))
            else:
                # Dispatcher call - return envelope
                print(json.dumps({
                    "ok": True,
                    "stdout": response
                }))
        else:
            # Standalone mode - print response directly
            print(response)
    
    except Exception as e:
        if not sys.stdin.isatty():
            if return_blob:
                # Pipe call - return blob error
                print(json.dumps({
                    "kind": "error",
                    "content": f"Error: {e}",
                    "meta": {"command": command}
                }))
            else:
                # Dispatcher call - return envelope error
                print(json.dumps({
                    "ok": False,
                    "error": {
                        "code": "EXECUTION_ERROR",
                        "message": str(e)
                    }
                }))
        else:
            # Standalone mode - print error directly
            print(f"Error: {e}")


def _build_chat_preprompt(session: SessionManager, current_query: str, is_piped_input: bool = False) -> str:
    """
    Build context-aware preprompt for chat mode with conversation history.
    
    Includes:
    - System context (OS, shell, current directory)
    - User preferences
    - Recent chat history (for memory)
    - Special mode for piped data analysis
    """
    # Get system context
    shell_name = 'PowerShell'  # Default for Windows
    if hasattr(session, 'shell_adapter') and session.shell_adapter:
        shell_name = session.shell_adapter.__class__.__name__.replace('Adapter', '')
    
    current_dir = Path.cwd()
    
    # Special preprompt for piped input - focus on data analysis
    if is_piped_input:
        preprompt = f"""You are Isaac, an AI assistant analyzing data piped from a previous command.

CRITICAL INSTRUCTIONS:
- The user has piped data from another command and is asking a question about that specific data
- Focus ONLY on analyzing the provided data to answer their question
- DO NOT suggest shell commands or PowerShell syntax
- DO NOT give generic advice about using commands
- Answer their specific question using ONLY the data provided

The data is in the query below, followed by the user's question.
Analyze the data and answer the question directly.
"""
    else:
        # Regular chat mode preprompt
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
