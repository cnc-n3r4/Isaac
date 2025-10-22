#!/usr/bin/env python3
"""
/ask command - Direct AI chat interface.

Unlike translation mode (isaac <query>), this sends queries directly to AI
and returns text responses without executing commands.
"""
from typing import Optional

import sys
import json
from pathlib import Path

# Add isaac package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.ai.xai_client import XaiClient
from isaac.ai.xai_collections_client import XaiCollectionsClient
from isaac.core.session_manager import SessionManager


def _classify_query_intent(query: str) -> tuple[str, Optional[str]]:
    """
    Classify user query intent and determine collection.
    
    Returns:
        ('intent', 'collection_name')
        - intent: 'file_history' | 'chat'
        - collection: 'tc_logs' | 'cpf_logs' | None
    """
    query_lower = query.lower()
    
    # CPF-specific keywords (project snapshots, backups)
    cpf_keywords = ['snapshot', 'cpf', 'project backup', 'image backup']
    if any(kw in query_lower for kw in cpf_keywords):
        return ('file_history', 'cpf_logs')
    
    # TC file operation keywords
    tc_keywords = [
        'moved', 'copied', 'deleted', 'renamed',
        'transfer', 'file', 'folder', 'directory'
    ]
    if any(kw in query_lower for kw in tc_keywords):
        return ('file_history', 'tc_logs')
    
    # Generic history questions - use default collection
    history_keywords = [
        'where did i', 'when did i', 'show me', 'find',
        'last week', 'yesterday', 'ago'
    ]
    if any(kw in query_lower for kw in history_keywords):
        return ('file_history', 'tc_logs')  # Default to TC logs
    
    # Regular chat
    return ('chat', None)


def _search_file_history(query: str, collection_name: Optional[str], 
                         config: dict, session: SessionManager) -> str:
    """
    Search file history logs via xAI Collections.
    
    Args:
        query: Natural language search query
        collection_name: 'tc_logs' | 'cpf_logs'
        config: Configuration dict
        session: SessionManager instance
    
    Returns formatted response with file operation results.
    """
    # Get Collections config
    api_key = config.get('xai_api_key') or config.get('api_key')
    
    if not api_key:
        return "Error: xAI API key not configured. Set it in ~/.isaac/config.json"
    
    if not collection_name:
        return "Error: No collection specified for file history search"
    
    # Map collection name to UUID
    collection_map = {
        'tc_logs': config.get('tc_log_collection_id'),
        'cpf_logs': config.get('cpf_log_collection_id')
    }
    
    collection_id = collection_map.get(collection_name)
    
    if not collection_id:
        return (f"Error: {collection_name} collection not configured. "
                f"Set '{collection_name}_collection_id' in ~/.isaac/config.json")
    
    try:
        # Initialize Collections client
        collections = XaiCollectionsClient(api_key=api_key)
        
        # Search collection
        results = collections.search_collection(
            collection_id=collection_id,
            query=query,
            top_k=5
        )
        
        # Format response
        if not results.get('results'):
            return "I couldn't find any matching file operations in your logs."
        
        response = "Here's what I found in your file history:\n\n"
        
        for i, result in enumerate(results['results'], 1):
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            score = result.get('score', 0)
            
            response += f"{i}. {content}\n"
            if metadata.get('timestamp'):
                response += f"   Date: {metadata['timestamp']}\n"
            response += f"   (Relevance: {score:.2%})\n\n"
        
        return response.strip()
        
    except Exception as e:
        # Fallback to chat mode if Collections fails
        return f"Collections search unavailable: {e}\n\nTrying chat mode instead..."


def _handle_chat_query(query: str, config: dict, session: SessionManager) -> str:
    """Handle regular chat queries (existing logic)"""
    # Get API configuration
    api_key = config.get('xai_api_key') or config.get('api_key')
    
    if not api_key:
        raise Exception("xAI API key not configured. Set it in ~/.isaac/config.json")
    
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
        # Read payload from stdin
        payload = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}
        
        # Extract query from the command string
        # Dispatcher provides: {"command": "/ask where is iowa?", "args": {...}, ...}
        command = payload.get('command', '')
        
        # Strip the trigger to get the query
        query = ''
        if command.startswith('/ask '):
            query = command[5:].strip()
        elif command.startswith('/a '):
            query = command[3:].strip()
        
        if not query:
            print(json.dumps({
                "ok": False,
                "kind": "text",
                "stdout": "Error: No query provided. Usage: /ask <question>",
                "meta": {}
            }))
            return
        
        # Get session
        session = SessionManager()
        
        # Get API configuration
        config = session.get_config()
        api_key = config.get('xai_api_key') or config.get('api_key')
        
        if not api_key:
            print(json.dumps({
                "ok": False,
                "kind": "text",
                "stdout": "Error: xAI API key not configured. Set it in ~/.isaac/config.json",
                "meta": {}
            }))
            return
        
        # Initialize xAI client
        client = XaiClient(
            api_key=api_key,
            api_url=config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
            model=config.get('xai_model', 'grok-3')
        )
        
        # Classify query intent and determine collection
        intent, collection_name = _classify_query_intent(query)
        
        if intent == 'file_history':
            # Route to Collections search
            response = _search_file_history(query, collection_name, config, session)
        else:
            # Route to chat mode (existing logic)
            response = _handle_chat_query(query, config, session)
        
        # Log query to AI history
        session.log_ai_query(
            query=query,
            translated_command='[chat_mode]' if intent == 'chat' else '[collection_search]',
            explanation=response[:100],
            executed=False,
            shell_name=intent
        )
        
        # Return response
        print(json.dumps({
            "ok": True,
            "kind": "text",
            "stdout": response,
            "meta": {"intent": intent}
        }))
    
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "kind": "text",
            "stdout": f"Error: {e}",
            "meta": {}
        }))


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
