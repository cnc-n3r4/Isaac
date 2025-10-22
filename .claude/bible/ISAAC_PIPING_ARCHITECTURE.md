# Isaac Piping Architecture - Unix Philosophy for Personal AI Shell

## Vision Statement
Isaac is a composable data-flow shell where commands transform data blobs through pipelines. Like Unix pipes but designed for AI-assisted personal workflows.

**Core Principle:** Each command is a tool that reads structured data, transforms it, and outputs structured data. Commands compose naturally via pipe operator.

---

## Pipe Operator Syntax

**Primary Syntax:** `|` (Unix-style pipe character)

```bash
/mine dig "deleted files" | /filter "4000" | /save cleanup_report.txt
/ask "what is kubernetes?" | /summarize | /save k8s_notes.md
/mine dig "backups" | /analyze trends | /chart bar_graph.png
```

**Parser Behavior:**
- Split command string on `|` boundaries (respect quotes)
- Trim whitespace from each segment
- First segment is input command, subsequent segments are transformers
- Final segment receives output from chain

**Escape Mechanism:** Quote protection
```bash
/ask "What is pipe | operator?" | /save notes.txt  # Quotes protect internal pipes
```

---

## Hybrid Shell/Isaac Piping

**Philosophy:** Don't reinvent the wheel. Unix has `grep`, `wc`, `sed`, `awk` - use them! PowerShell has `Select-String`, `Measure-Object` - use them! Isaac commands (`/save`, `/analyze`, etc.) integrate seamlessly with native shell tools.

**Command Detection:**
- Starts with `/` → Isaac command (route to plugin handler)
- No `/` prefix → Shell command (execute via shell adapter)

**Examples:**

```bash
# Use native grep instead of /filter
ls -la | grep ".py" | /save python_list.txt

# Mix freely
cat data.csv | /analyze "find trends" | grep "important" | /save summary.txt

# Isaac queries feed shell tools
# Isaac → Shell  
/mine dig "errors" | grep "4000" | wc -l

# Shell output to Isaac
Get-Process | /save processes.txt

# Complex hybrid chains
find . -name "*.log" | /mine cast | /count
# Mixed
**Examples:**
- Shell → Isaac: `ls | /save`
- Isaac → shell: `/mine dig | grep`
- Mixed: `cat log | /analyze | grep "memory" | /save diagnosis.md`
find . -name "*.log" | /mine cast
```

**Data Flow:**
- **Shell → Isaac:** Plain text stdout becomes text blob content
- **Isaac → Shell:** Blob content extracted to stdin for shell command
- **Shell → Shell:** Normal pipe behavior (Isaac transparent)

**Implementation Pattern:**
```python
def _execute_command(self, cmd: str, stdin_blob: dict = None) -> dict:
    """Execute command - detect Isaac vs shell"""
    if cmd.strip().startswith('/'):
        # Isaac command - pass blob
        return self._execute_isaac_command(cmd, stdin_blob)
    else:
        # Shell command - extract text content from blob
        stdin_text = stdin_blob['content'] if stdin_blob else None
        result = self.shell_adapter.execute(cmd, stdin=stdin_text)
        
        # Wrap shell output as text blob
        return {
            "kind": "text",
            "content": result.output,
            "meta": {
                "source_command": cmd,
                "exit_code": result.exit_code,
                "shell": self.shell_adapter.name
            }
        }
```

**Benefits:**
- Users leverage existing shell knowledge
- No need to reimplement `grep`, `sed`, `awk`, `wc`, etc.
- Isaac commands add AI/cloud capabilities shell lacks
- Gradual learning curve: start with familiar tools, add Isaac powers

**Platform Notes:**
- PowerShell: `Select-String` instead of `grep`, `Measure-Object` instead of `wc`
- Bash/Zsh: Standard Unix tools work as expected
- Shell adapter abstracts differences

---

## Data Blob Format

**JSON Envelope Structure:**
```json
{
  "kind": "text|json|binary|error",
  "content": "<primary payload>",
  "meta": {
    "source_command": "/mine dig",
    "timestamp": "2025-10-22T14:30:00Z",
    "encoding": "utf-8",
    "mime_type": "text/plain",
    "size_bytes": 1024
  }
}
```

**Blob Types:**

1. **Text Blob** (`kind: "text"`):
```json
{
  "kind": "text",
  "content": "Search results:\n- file1.txt deleted\n- file2.log removed",
  "meta": {"source_command": "/mine dig", "line_count": 2}
}
```

2. **JSON Blob** (`kind: "json"`):
```json
{
  "kind": "json",
  "content": {"files": ["a.txt", "b.log"], "total": 2},
  "meta": {"source_command": "/mine dig", "schema": "file_list"}
}
```

3. **Binary Blob** (`kind: "binary"`):
```json
{
  "kind": "binary",
  "content": "<base64_encoded_data>",
  "meta": {"mime_type": "image/png", "encoding": "base64"}
}
```

4. **Error Blob** (`kind: "error"`):
```json
{
  "kind": "error",
  "content": "Collection not found: tc_logs",
  "meta": {"error_code": "COLLECTION_NOT_FOUND", "recoverable": false}
}
```

**Hybrid Mode:** Shell commands output plain text, pipe engine auto-wraps into text blob.

---

## Plugin Interface Contract

**Pipe-Compatible Command Requirements:**

1. **Standard Input:** Read JSON blob from stdin
2. **Standard Output:** Write JSON blob to stdout  
3. **Error Handling:** Return error blob on failure, don't crash
4. **Stateless:** No side effects unless explicit (like `/save`)
5. **Manifest Declaration:** `command.yaml` declares pipe compatibility

**Example Manifest (`/save/command.yaml`):**
```yaml
name: save
trigger: /save
summary: Save output to file
pipe_compatible: true
stdin_blob_types: ["text", "json", "binary"]
stdout_blob_type: "text"
timeout_ms: 5000
```

**Plugin API Pattern:**
```python
class SaveHandler:
    def handle_piped_input(self, blob: dict, args: List[str]) -> dict:
        """Process blob and return transformed blob"""
        if not args:
            return {"kind": "error", "content": "Usage: /save <file>"}
        
        file_path = args[0]
        content = blob.get('content', '')
        
        Path(file_path).write_text(content)
        
        return {
            "kind": "text",
            "content": f"Saved {len(content)} bytes to {file_path}",
            "meta": {"saved_file": file_path, "size_bytes": len(content)}
        }
```

---

## Core Isaac Commands (Focus on AI/Cloud Capabilities)

Isaac commands provide capabilities that shell lacks. Don't reimplement native tools.

### Tier 1: Essential Isaac Utilities

**`/save <file>`**
- Purpose: Intelligent file saving (auto-naming, versioning, cloud sync)
- Input: Any blob type
- Output: Confirmation message (kind: "text")
- Example: `/mine dig "foo" | /save results.txt`

**`/analyze [prompt]`**
- Purpose: AI analysis of previous output
- Input: Any blob type (text, json)
- Output: AI insights as text blob
- Example: `cat error.log | /analyze "what caused these errors?"`

**`/summarize [length]`**
- Purpose: AI summarization (short, medium, long)
- Input: Text blob
- Output: Condensed text blob
- Example: `/ask "explain kubernetes" | /summarize short | /save k8s.md`

### Tier 2: AI Enhancement Commands

**`/translate <lang>`**
- Purpose: Translate text to target language
- Input: Text blob
- Output: Translated text blob
- Example: `/ask "hello world" | /translate spanish`

**`/extract <pattern>`**
- Purpose: AI-powered data extraction
- Input: Text or JSON blob
- Output: Extracted data as JSON blob
- Example: `cat emails.txt | /extract "email addresses" | /save contacts.json`

**`/compare <blob1> <blob2>`**
- Purpose: AI-powered diff/comparison
- Input: Two blobs
- Output: Comparison report text blob
- Example: Future enhancement for comparing Collections results

### Tier 3: Visualization & Formatting

**`/format <type>`**
- Purpose: Pretty-print output (json, markdown, table, etc.)
- Input: Text or JSON blob
- Output: Formatted text blob
- Example: `/mine dig "logs" | /format table`

**`/chart <type> <file>`**
- Purpose: Generate visualization from data
- Input: JSON blob with numeric data
- Output: Binary blob (PNG/SVG) saved to file
- Example: `/mine dig "usage stats" | /extract numbers | /chart bar usage.png`

**`/alert [condition]`**
- Purpose: Send notification if condition met
- Input: Any blob
- Output: Pass-through blob + side-effect notification
- Example: `/mine dig "errors" | /alert "if count > 10"`

---

## Cross-Platform Command Aliases (Phase 2 Enhancement)

**Problem:** Unix users on Windows forget PowerShell syntax. PowerShell is powerful but verbose.

**Solution:** Isaac provides optional aliases that translate familiar Unix commands to PowerShell equivalents.

**Alias Types:**

### 1. Unix-to-PowerShell Translation
```bash
# User types Unix syntax (Isaac detects and translates if command not found)
grep "error" log.txt          # → Select-String "error" log.txt
find . -name "*.py"           # → Get-ChildItem -Recurse -Filter "*.py"
ps aux                        # → Get-Process | Format-Table
kill 1234                     # → Stop-Process -Id 1234
cat file.txt                  # → Get-Content file.txt
ls -la                        # → Get-ChildItem | Format-List
wc -l file.txt                # → Measure-Object -Line file.txt
```

**Detection:** If command not found in shell, check alias table before erroring.

### 2. Convenience Shortcuts
```bash
/grep <pattern> [file]        # PowerShell: Select-String, Bash: grep
/find <path> <pattern>        # PowerShell: Get-ChildItem, Bash: find
/ps [filter]                  # PowerShell: Get-Process, Bash: ps
/kill <pid>                   # PowerShell: Stop-Process, Bash: kill
```

**Benefits:**
- Users don't fight muscle memory
- PowerShell becomes accessible to Unix users
- Gradual learning (see translated command in output)
- No reinventing grep/find/ps/wc/etc.

**Configuration:**
```json
{
  "enable_unix_aliases": true,
  "show_translated_command": true,
  "alias_overrides": {
    "grep": "custom-grep-script"
  }
}
```

**Alias Table (`isaac/data/unix_aliases.json`):**
```json
{
  "grep": {
    "powershell": "Select-String",
    "bash": "grep",
    "description": "Search text patterns"
  },
  "find": {
    "powershell": "Get-ChildItem -Recurse",
    "bash": "find",
    "description": "Find files"
  },
  "ps": {
    "powershell": "Get-Process",
    "bash": "ps",
    "description": "List processes"
  },
  "kill": {
    "powershell": "Stop-Process",
    "bash": "kill",
    "description": "Terminate process"
  },
  "cat": {
    "powershell": "Get-Content",
    "bash": "cat",
    "description": "Display file content"
  },
  "ls": {
    "powershell": "Get-ChildItem",
    "bash": "ls",
    "description": "List directory"
  },
  "wc": {
    "powershell": "Measure-Object -Line -Word -Character",
    "bash": "wc",
    "description": "Count lines/words/chars"
  },
  "head": {
    "powershell": "Select-Object -First",
    "bash": "head",
    "description": "First N lines"
  },
  "tail": {
    "powershell": "Select-Object -Last",
    "bash": "tail",
    "description": "Last N lines"
  },
  "which": {
    "powershell": "Get-Command",
    "bash": "which",
    "description": "Locate command"
  }
}
```

**Implementation Hook:**
```python
def route_command(self, user_input: str) -> dict:
    # 1. Check for Isaac commands first (/ prefix)
    if user_input.startswith('/'):
        return self._execute_isaac_command(user_input)
    
    # 2. Check for pipe operator
    if '|' in user_input:
        return self.pipe_engine.execute_pipeline(user_input)
    
    # 3. Try native shell execution
    result = self.shell_adapter.execute(user_input)
    if result.success:
        return result
    
    # 4. Command not found - check Unix alias table (Phase 2)
    if self._is_windows() and self._unix_aliases_enabled():
        translated = self._try_unix_alias_translation(user_input)
        if translated:
            if self._show_translated_command():
                print(f"[Translated: {translated}]")
            return self.shell_adapter.execute(translated)
    
    # 5. Command not found
    return error_result(f"Command not found: {user_input}")
```

**User Experience:**
```powershell
$> grep "error" app.log
[Translated: Select-String "error" app.log]
app.log:42: Error: Connection timeout

$> find . -name "*.py" | /count
[Translated: Get-ChildItem -Recurse -Filter "*.py"]
Found 47 Python files
```

**Design Decisions:**
- **Optional:** Can be disabled if user prefers pure PowerShell
- **Transparent:** Show translated command for learning
- **Non-intrusive:** Only activates on "command not found"
- **Extensible:** User can add custom aliases
- **Intelligent:** Detect shell type, translate appropriately

---

## Pipe Engine Implementation

**Location:** `isaac/core/pipe_engine.py`

**Core Logic:**
```python
class PipeEngine:
    def __init__(self, session_manager, shell_adapter):
        self.session_manager = session_manager
        self.shell_adapter = shell_adapter
    
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
    
    def _parse_pipe_segments(self, cmd: str) -> List[str]:
        """Split on | respecting quoted strings"""
        # Use shlex or custom parser to handle quotes
        import shlex
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
    
    def _execute_command(self, cmd: str, stdin_blob: dict = None) -> dict:
        """Execute Isaac or shell command appropriately"""
        if cmd.startswith('/'):
            # Isaac command
            return self._execute_isaac_command(cmd, stdin_blob)
        else:
            # Shell command
            return self._execute_shell_command(cmd, stdin_blob)
    
    def _execute_isaac_command(self, cmd: str, stdin_blob: dict = None) -> dict:
        """Execute Isaac plugin with blob I/O"""
        # Pass full blob to Isaac command via stdin JSON
        # Use existing dispatcher logic
        from isaac.core.command_router import CommandRouter
        router = CommandRouter(self.session_manager)
        return router.execute_with_blob(cmd, stdin_blob)
    
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

**Integration Point:** `isaac/core/command_router.py`
```python
def route_command(self, user_input: str) -> dict:
    if '|' in user_input and not self._is_quoted_pipe(user_input):
        from isaac.core.pipe_engine import PipeEngine
        engine = PipeEngine(self.session_manager, self.shell_adapter)
        return engine.execute_pipeline(user_input)
    else:
        return self._execute_single_command(user_input)
```

---

## Error Handling in Pipelines

**Propagation Strategy:**
- Error blob stops pipeline execution immediately
- Partial results are lost (no intermediate saves)
- Error message includes failing command and reason

**Example Error Flow:**
```bash
**Example Error Pipeline:**
```bash
/mine dig "foo" | /filter "bar" | /nonexistent | /save out.txt
```

# Pipeline stops at /nonexistent:
{
  "kind": "error",
  "content": "Unknown command: /nonexistent",
  "meta": {
    "failed_command": "/nonexistent",
    "pipeline_position": 3,
    "partial_input": "<blob from /filter>"
  }
}
```

**Recovery Options:**
- User sees error, can fix command and retry
- Future enhancement: `/rescue` command to capture partial results

---

## Extensibility Model

**User Plugins:** Drop YAML + Python in `~/.isaac/plugins/`
```
~/.isaac/plugins/
  myfilter/
    command.yaml
    run.py
```

**Auto-Registration:** Dispatcher scans plugin directory at startup, validates manifests, loads handlers.

**Plugin Guidelines:**
- Prefer stateless transforms
- Document input/output blob types
- Handle errors gracefully (return error blob)
- Respect timeout limits
- Keep plugins focused (single responsibility)

---

## Future Enhancements

**Planned Features:**
- **Parallel pipes:** `(cmd1 | cmd2) & (cmd3 | cmd4) | merge`
- **Conditional pipes:** `cmd1 | if-error /alert else /save`
- **Named pipes:** `cmd1 | store:result | cmd2 | load:result | combine`
- **Streaming:** Large datasets stream through pipes chunk-by-chunk
- **Pipe history:** Recall previous pipeline for editing/re-execution

**Integration Ideas:**
- Chain `/mine` searches: `/mine use tc_logs | query "foo" | mine use cpf_logs | query "bar" | compare`
- Multi-AI collaboration: `/ask grok "X" | /ask claude "critique this" | /merge_answers`
- Workflow automation: Save common pipelines as named aliases

---

## Design Decisions & Rationale

**Why JSON Blobs?**
- Structured data enables rich transformations
- Metadata preserves provenance through chain
- Type-safe plugin interfaces
- Backward compatible: plain text auto-wraps to text blob

**Why `|` Operator?**
- Familiar to Unix users (muscle memory)
- Visually clear pipeline direction
- Easy to parse (single character)
- Consistent with shell conventions

**Why Hybrid Shell/Isaac?**
- Don't reinvent grep, wc, sed, awk
- Users already know native tools
- Focus Isaac on AI/cloud capabilities
- Smaller codebase, faster development

**Why Stateless Plugins?**
- Easier to reason about
- No hidden dependencies
- Parallelizable in future
- Testable in isolation

**Why Stop on Error?**
- Fail-fast prevents silent data corruption
- User gets immediate feedback
- Simpler mental model than partial execution
- Consistent with Unix pipe behavior (SIGPIPE)

**Why Unix Alias System?**
- Accessibility: PowerShell powerful but verbose
- Muscle memory: Unix users on Windows shouldn't suffer
- Learning aid: Show translated commands
- Optional: Can be disabled

---

## Implementation Timeline

**Phase 1: Core Hybrid Engine (Week 1)**
- Pipe parser with quote handling
- PipeEngine execution loop (Isaac + shell commands)
- Blob format validation
- Integration with command_router
- Shell adapter stdin support
- Essential commands: `/save`, `/analyze`, `/summarize`

**Phase 2: Unix Alias System (Week 2)**
- Unix-to-PowerShell alias table
- Command router fallback hook
- Translation logic with arg mapping
- User configuration options
- Show translated command feature

**Phase 3: AI Commands (Week 3)**
- `/translate`, `/extract`, `/compare`
- xAI integration for piped AI calls
- Blob type conversions

**Phase 4: Utilities & Polish (Week 4)**
- `/format`, `/chart`, `/alert`
- Plugin loading system
- Documentation and examples
- User plugin guide

---

## Testing Strategy

**Unit Tests:**
- Pipe segment parsing with quotes
- Isaac vs shell command detection
- Blob format validation
- Error propagation
- Alias translation logic

**Integration Tests:**
- Shell → Isaac: `ls | /save`
- Isaac → shell: `/mine dig | grep`
- Mixed chain: `cat | /analyze | grep | /save`
- Error handling in pipelines
- Unix alias translation on Windows

**Performance Tests:**
- Large text blobs through pipes
- Complex multi-stage pipelines
- Shell command overhead

**Coverage Target:** ≥85%

---

**Status:** DESIGN FINALIZED - Ready for Implementation  
**Next Step:** Coding agent implements Phase 1 (Hybrid Pipe Engine)  
**Dependencies:** Shell adapter stdin support required

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Author:** Sarah (Visual Persona)
