# Piping System Implementation - Phase 1: Hybrid Pipe Engine

## Objective
Implement hybrid pipe operator that seamlessly mixes Isaac commands (`/cmd`) with native shell commands (`grep`, `ls`, `Get-Process`, etc.).

## Key Innovation
**Don't reinvent Unix/PowerShell.** Users already know `grep`, `wc`, `sed`, `Select-String`, `Measure-Object`. Isaac adds AI/cloud superpowers on top, doesn't replace shell fundamentals.

## Design Reference
See `.claude/bible/ISAAC_PIPING_ARCHITECTURE.md` for complete specification.

## Implementation Tasks

### 1. Create Hybrid PipeEngine Module
**File:** `isaac/core/pipe_engine.py`

**Command Detection Logic:**
```python
def _is_isaac_command(self, cmd: str) -> bool:
    """Check if command is Isaac plugin or shell command"""
    return cmd.strip().startswith('/')

def _execute_command(self, cmd: str, stdin_blob: dict = None) -> dict:
    """Execute Isaac or shell command appropriately"""
    if self._is_isaac_command(cmd):
        # Route to Isaac plugin system
        return self._execute_isaac_command(cmd, stdin_blob)
    else:
        # Execute via shell adapter
        return self._execute_shell_command(cmd, stdin_blob)
```

**Pipe Segment Parser:**
```python
def _parse_pipe_segments(self, cmd: str) -> List[str]:
    """Split on | respecting quoted strings"""
    segments = []
    current = []
    in_quotes = False
    quote_char = None
    
    for char in cmd:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
            current.append(char)
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
            current.append(char)
        elif char == '|' and not in_quotes:
            segments.append(''.join(current).strip())
            current = []
        else:
            current.append(char)
    
    if current:
        segments.append(''.join(current).strip())
    
    return segments
```

**Shell Command Execution:**
```python
def _execute_shell_command(self, cmd: str, stdin_blob: dict = None) -> dict:
    """Execute native shell command with blob I/O"""
    # Extract text content from blob for shell stdin
    stdin_text = None
    if stdin_blob:
        if stdin_blob['kind'] == 'text':
            stdin_text = stdin_blob['content']
        elif stdin_blob['kind'] == 'json':
            # Convert JSON to pretty-printed text
            import json
            stdin_text = json.dumps(stdin_blob['content'], indent=2)
        elif stdin_blob['kind'] == 'error':
            # Propagate error, don't execute
            return stdin_blob
    
    # Execute via shell adapter
    result = self.shell_adapter.execute(cmd, stdin=stdin_text)
    
    # Wrap result as blob
    if result.success:
        return {
            "kind": "text",
            "content": result.output,
            "meta": {
                "source_command": cmd,
                "exit_code": result.exit_code,
                "shell": self.shell_adapter.name
            }
        }
    else:
        return {
            "kind": "error",
            "content": result.output or f"Command failed: {cmd}",
            "meta": {
                "exit_code": result.exit_code,
                "failed_command": cmd
            }
        }
```

**Isaac Command Execution:**
```python
def _execute_isaac_command(self, cmd: str, stdin_blob: dict = None) -> dict:
    """Execute Isaac plugin with blob I/O"""
    # Pass full blob to Isaac command via stdin JSON
    # Isaac commands understand blob format
    # Use existing dispatcher logic
    from isaac.core.command_router import CommandRouter
    router = CommandRouter(self.session_manager)
    return router.execute_with_blob(cmd, stdin_blob)
```

**Main Pipeline Execution:**
```python
def execute_pipeline(self, command_string: str) -> dict:
    """Parse and execute piped command chain"""
    # 1. Split on | boundaries (respect quotes)
    segments = self._parse_pipe_segments(command_string)
    
    # 2. Execute first command (source)
    blob = self._execute_command(segments[0])
    
    # 3. Chain through transformers
    for segment in segments[1:]:
        if blob['kind'] == 'error':
            break  # Stop on error
        blob = self._execute_command(segment, stdin_blob=blob)
    
    # 4. Return final blob
    return blob
```

### 2. Update Shell Adapters for Stdin Support
**Files:** `isaac/adapters/powershell_adapter.py`, `isaac/adapters/bash_adapter.py`

**Add stdin parameter to execute method:**
```python
def execute(self, command: str, stdin: str = None) -> CommandResult:
    """Execute command with optional stdin text"""
    import subprocess
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE if stdin else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        stdout, stderr = process.communicate(input=stdin)
        
        return CommandResult(
            success=(process.returncode == 0),
            output=stdout or stderr,
            exit_code=process.returncode
        )
    except Exception as e:
        return CommandResult(
            success=False,
            output=str(e),
            exit_code=-1
        )
```

### 3. Update Command Router for Pipe Detection
**File:** `isaac/core/command_router.py`

**Add pipe detection in route_command:**
```python
def route_command(self, user_input: str) -> dict:
    # Check for pipe operator (not in quotes)
    if '|' in user_input and not self._is_quoted_pipe(user_input):
        from isaac.core.pipe_engine import PipeEngine
        engine = PipeEngine(self.session_manager, self.shell_adapter)
        result_blob = engine.execute_pipeline(user_input)
        
        # Convert blob to display format
        if result_blob['kind'] == 'error':
            return {"ok": False, "stdout": result_blob['content']}
        else:
            return {"ok": True, "stdout": result_blob['content']}
    else:
        # Existing single command logic
        return self._execute_single_command(user_input)

def _is_quoted_pipe(self, cmd: str) -> bool:
    """Check if all pipes are inside quotes"""
    in_quotes = False
    quote_char = None
    
    for char in cmd:
        if char in ('"', "'") and not in_quotes:
            in_quotes = True
            quote_char = char
        elif char == quote_char and in_quotes:
            in_quotes = False
            quote_char = None
        elif char == '|' and not in_quotes:
            return False  # Found pipe outside quotes
    
    return True  # All pipes are quoted
```

### 4. Update Existing Commands for Blob I/O

**Pattern for all Isaac commands:**
```python
def main():
    """Main entry point with blob I/O support"""
    try:
        if not sys.stdin.isatty():
            input_data = json.loads(sys.stdin.read())
            
            # Check if it's a blob (has 'kind' field)
            if 'kind' in input_data:
                # Piped input - process blob
                result_blob = handle_piped_input(input_data)
                print(json.dumps(result_blob))
                return
            
            # Otherwise it's dispatcher envelope
            payload = input_data
        else:
            # Standalone execution
            payload = {"command": " ".join(sys.argv)}
        
        # Normal command handling
        result = handle_command(payload)
        
        # Wrap in blob for pipe compatibility
        blob = {
            "kind": "text",
            "content": result,
            "meta": {"source_command": payload.get('command')}
        }
        print(json.dumps(blob))
    
    except Exception as e:
        error_blob = {
            "kind": "error",
            "content": str(e),
            "meta": {}
        }
        print(json.dumps(error_blob))
```

### 5. Implement Essential Isaac Utility Commands

#### `/save <file>` Command
**File:** `isaac/commands/save/run.py`
**File:** `isaac/commands/save/command.yaml`

**Behavior:**
- Read blob from stdin
- Extract content field
- Write to specified file path
- Return confirmation blob

**Implementation:**
```python
def handle_piped_input(blob: dict, args: List[str]) -> dict:
    """Save blob content to file"""
    if not args:
        return {"kind": "error", "content": "Usage: /save <file>"}
    
    file_path = Path(args[0]).expanduser()
    content = blob.get('content', '')
    
    # Handle different blob types
    if blob['kind'] == 'json':
        import json
        content = json.dumps(blob['content'], indent=2)
    elif blob['kind'] == 'binary':
        import base64
        content = base64.b64decode(blob['content'])
        file_path.write_bytes(content)
        return {
            "kind": "text",
            "content": f"Saved {len(content)} bytes to {file_path}",
            "meta": {"saved_file": str(file_path), "size_bytes": len(content)}
        }
    
    # Text content
    file_path.write_text(content)
    
    return {
        "kind": "text",
        "content": f"Saved to {file_path}",
        "meta": {"saved_file": str(file_path), "size_bytes": len(content)}
    }
```

#### `/analyze [prompt]` Command
**File:** `isaac/commands/analyze/run.py`
**File:** `isaac/commands/analyze/command.yaml`

**Behavior:**
- Read blob from stdin (text or json)
- Send to AI with optional analysis prompt
- Return AI insights as text blob

**Implementation:**
```python
def handle_piped_input(blob: dict, args: List[str]) -> dict:
    """AI analysis of blob content"""
    content = blob.get('content', '')
    prompt = " ".join(args) if args else "Analyze this data and provide insights"
    
    # Convert JSON to text if needed
    if blob['kind'] == 'json':
        import json
        content = json.dumps(blob['content'], indent=2)
    
    # Get AI analysis
    from isaac.ai.xai_client import XaiClient
    from isaac.core.session_manager import SessionManager
    
    session = SessionManager()
    xai = XaiClient(session)
    
    full_prompt = f"{prompt}\n\nData:\n{content}"
    analysis = xai.chat_completion(full_prompt)
    
    return {
        "kind": "text",
        "content": analysis,
        "meta": {
            "source_command": "/analyze",
            "analysis_prompt": prompt,
            "input_size": len(content)
        }
    }
```

#### `/summarize [length]` Command
**File:** `isaac/commands/summarize/run.py`
**File:** `isaac/commands/summarize/command.yaml`

**Behavior:**
- Read text blob from stdin
- AI summarization (short, medium, long)
- Return summary as text blob

**Implementation:**
```python
def handle_piped_input(blob: dict, args: List[str]) -> dict:
    """AI summarization of text"""
    if blob['kind'] not in ['text', 'json']:
        return {"kind": "error", "content": "Summarize requires text or JSON input"}
    
    content = blob.get('content', '')
    if blob['kind'] == 'json':
        import json
        content = json.dumps(blob['content'], indent=2)
    
    length = args[0] if args else "medium"
    if length not in ["short", "medium", "long"]:
        length = "medium"
    
    # Get AI summary
    from isaac.ai.xai_client import XaiClient
    from isaac.core.session_manager import SessionManager
    
    session = SessionManager()
    xai = XaiClient(session)
    
    prompt = f"Provide a {length} summary of the following:\n\n{content}"
    summary = xai.chat_completion(prompt)
    
    return {
        "kind": "text",
        "content": summary,
        "meta": {
            "source_command": "/summarize",
            "summary_length": length,
            "input_size": len(content)
        }
    }
```

### 6. Integration Examples

**Example 1: Shell → Isaac**
```bash
ls -la | /save file_list.txt
Get-Process | /save processes.txt
```

**Example 2: Isaac → Shell**
```bash
/mine dig "deleted files" | grep "4000" | wc -l
/ask "explain pipes" | Select-String "Unix"
```

**Example 3: Hybrid Chain**
```bash
cat error.log | /analyze "what caused this?" | grep "memory" | /save diagnosis.md
dir *.log | /mine cast | Select-String "success"
```

## Testing Requirements

**Unit Tests:** `tests/test_pipe_engine.py`
- Test pipe segment parsing with quotes
- Test Isaac vs shell command detection
- Test blob format creation/validation
- Test error propagation

**Unit Tests:** `tests/test_shell_stdin.py`
- Test shell adapter stdin parameter
- Test PowerShell vs bash stdin differences
- Test empty stdin, large stdin

**Integration Tests:** `tests/test_hybrid_piping.py`
- Test shell → Isaac: `ls | /save`
- Test Isaac → shell: `/mine dig | grep`
- Test mixed chain: `cat | /analyze | grep | /save`
- Test error handling in middle of chain
- Test blob type conversions (text ↔ shell stdin/stdout)

## Acceptance Criteria

✅ User can execute: `ls -la | /save files.txt`  
✅ User can execute: `/mine dig "foo" | grep "bar" | wc -l`  
✅ User can execute: `cat data.txt | /analyze | /save insights.md`  
✅ Shell commands execute via shell adapter with stdin support  
✅ Isaac commands receive properly formatted blobs  
✅ Error in any command stops pipeline with clear message  
✅ Blob metadata preserved through chain  
✅ Test coverage ≥85%

## Implementation Estimate
**Complexity:** Medium  
**Time:** 8-12 hours  
**Blockers:** None - shell adapter enhancement straightforward

**Note:** xAI Collections API is now working (authentication resolved Oct 22, 2025). `/mine` commands can be used in pipe examples.

## Benefits Over Pure Isaac Pipes
- Leverage existing shell knowledge (no learning curve)
- Don't reimplement Unix/PowerShell tools (grep, wc, sed, awk, Select-String, Measure-Object)
- Focus Isaac commands on AI/cloud/unique features
- Natural for Unix/PowerShell users
- Smaller codebase, faster development
- Cross-platform: Works on Windows PowerShell and Unix bash

## Next Phases
- Phase 2: Unix alias translation system (grep → Select-String on Windows)
- Phase 3: Additional AI commands (/translate, /extract, /compare)
- Phase 4: Visualization commands (/format, /chart, /alert)

---

**Status:** READY FOR IMPLEMENTATION  
**Dependencies:** Shell adapter stdin support (simple addition)  
**Handoff:** Coding agent can begin immediately

---

**Spec Version:** 1.0  
**Created:** October 22, 2025  
**Author:** Sarah (Visual Persona)
