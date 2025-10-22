# Isaac Command Reference - Complete Guide

**Last Updated:** October 22, 2025  
**Version:** Piping System Design Phase  
**Status:** Authoritative Reference

---

## Purpose

This is the single source of truth for ALL Isaac commands. Use this for:
- Learning the command system
- Writing documentation
- Testing new features
- Teaching others about Isaac

---

## Command Categories

### 1. Meta-Commands (Local Execution)
These execute immediately without tier validation. Handled by `isaac/commands/` modules.

| Command | Purpose | Example |
|---------|---------|---------|
| `/help` | Display command reference | `/help` |
| `/status` | Show system status | `/status` |
| `/config` | Modify configuration | `/config ai on` |
| `/clear` | Clear screen | `/clear` |
| `/exit` | Exit Isaac | `/exit` |

### 2. AI Commands (Session-Based)
AI-powered commands that remember context within your session.

#### `/ask <question>`
**Purpose:** Direct AI chat with session memory (last 5 queries)  
**Model:** grok-3 (xAI)  
**Session Memory:** Yes (AIQueryHistory)  
**Examples:**
```bash
/ask what is kubernetes?
/ask how do I use docker? # Remembers previous question
```

**Integration:**
- Can be piped: `/ask "foo" | /save`, `/ask "bar" | /summarize`
- Output: Text blob (AI response)

#### `/mine` - Personal File History Mining
**Purpose:** Search and manage your personal document Collections with AI  
**Backend:** xAI Collections API  
**Session Aware:** Yes (tracks active collection)

**Subcommands:**

##### `/mine cast <file> [name]`
**Purpose:** Cast documents down the mine (upload to Collections)  
**Metaphor:** Like casting ore down a mine shaft  
**Old Name:** `/mine upload` (still works as alias)  
**Examples:**
```bash
/mine cast ~/docs/api.pdf
/mine cast ./logs/*.txt backup_logs
/mine cast README.md -n project_docs
```

**Features:**
- Batch upload: `*.txt` patterns supported
- Auto-naming: Defaults to filename if name not provided
- Metadata: Tracks upload timestamp, file size

##### `/mine dig <question>`
**Purpose:** Dig up answers from your Collections with AI  
**Metaphor:** Like digging up ore/insights  
**Old Name:** `/mine query` (still works as alias)  
**Examples:**
```bash
/mine dig "where are the API docs?"
/mine dig "what errors happened on Oct 20?"
```

**Features:**
- Semantic search across all Collections
- AI-powered query understanding
- Context-aware results

**Chain Query (Planned):**
```python
# Collections.search() → chunks → Chat.completions.create()
chunks = collections.search(query)
response = chat.analyze(chunks + user_question)
```

##### `/mine use <collection_name>`
**Purpose:** Switch active collection context  
**Examples:**
```bash
/mine use tc_logs
/mine dig "session errors" # Searches only tc_logs now
```

##### `/mine ls`
**Purpose:** List all your Collections  
**Output:** Table with name, size, document count

##### `/mine init <name>`
**Purpose:** Create new Collection  
**Example:** `/mine init project_notes`

**Collections Configuration:**
```json
{
  "xai": {
    "collections": {
      "tc_logs": "uuid-tc-logs",
      "cpf_logs": "uuid-cpf-logs"
    }
  }
}
```

### 3. Piping Commands (Phase 1 - In Development)
Commands designed for data transformation pipelines.

#### `/save <file>`
**Purpose:** Save any blob type to disk  
**Input:** Text, JSON, or binary blob  
**Output:** Confirmation message  
**Examples:**
```bash
ls | /save dir_list.txt
/ask "kubernetes" | /save notes.md
/mine dig "errors" | /save findings.txt
```

**Features:**
- Auto-creates directories
- Detects blob type, writes appropriately
- Optional versioning (future)

#### `/analyze [prompt]`
**Purpose:** AI analysis of piped data  
**Input:** Any blob (text/JSON)  
**Output:** AI insights as text blob  
**Model:** grok-3  
**Examples:**
```bash
cat error.log | /analyze "what caused these?"
Get-Process | /analyze "which processes use most memory?"
/mine dig "crashes" | /analyze "find patterns"
```

**Features:**
- Contextual prompts optional
- Preserves original data in blob metadata
- Can chain: `| /analyze | /save`

#### `/summarize [length]`
**Purpose:** AI-powered text summarization  
**Input:** Text blob  
**Output:** Condensed text  
**Lengths:** short (2-3 sentences), medium (paragraph), long (multi-paragraph)  
**Examples:**
```bash
/ask "explain kubernetes" | /summarize short
cat report.txt | /summarize medium | /save executive_summary.md
```

### 4. Advanced Piping Commands (Phase 3 - Future)

#### `/translate <language>`
**Purpose:** Translate text to target language  
**Example:** `/ask "hello" | /translate spanish`

#### `/extract <pattern>`
**Purpose:** AI-powered data extraction  
**Example:** `cat emails.txt | /extract "email addresses" | /save contacts.json`

#### `/format <type>`
**Purpose:** Format output (json, table, markdown)  
**Example:** `/mine dig "logs" | /format table`

#### `/chart <type> <file>`
**Purpose:** Generate visualizations  
**Example:** `/mine dig "usage" | /extract numbers | /chart bar usage.png`

#### `/alert [condition]`
**Purpose:** Conditional notifications  
**Example:** `/mine dig "errors" | /alert "if count > 10"`

### 5. Shell Commands (No Prefix)
Standard shell commands execute normally. Isaac wraps your native shell (PowerShell/bash).

**Examples:**
```bash
ls -la
cd ~/projects
Get-Process | Where-Object CPU -gt 50
grep "error" *.log
```

---

## Piping Integration

### Hybrid Piping Philosophy
**Core Idea:** Mix native shell tools with Isaac AI commands freely.

**Command Detection:**
- **Starts with `/`** → Isaac command (plugin handler)
- **No `/` prefix** → Shell command (native execution)

### Real-World Examples

#### Shell → Isaac
```bash
ls | /save dir.txt
cat log.txt | /analyze
Get-Process | /summarize short
```

#### Isaac → Shell
```bash
/ask "list files" | grep ".py"
/mine dig "errors" | grep "4000" | wc -l
/mine cast report.pdf | Select-String "success"
```

#### Mixed Chains
```bash
# Complex analysis pipeline
cat data.csv | /analyze "trends" | grep "important" | /save summary.txt

# Collections + shell filtering
/mine dig "crashes" | grep "memory" | wc -l

# Batch operations
find . -name "*.log" | /mine cast | /count
```

### Data Blob Format
All Isaac commands use structured JSON blobs internally:

```json
{
  "kind": "text",
  "content": "actual data here",
  "meta": {
    "source_command": "/mine dig",
    "line_count": 150,
    "timestamp": "2025-10-22T10:30:00Z"
  }
}
```

**Blob Types:**
- `text` - Plain text output
- `json` - Structured data
- `binary` - Images, PDFs, etc.
- `error` - Error state (stops pipeline)

**Shell Integration:**
- Shell output → wrapped as text blob
- Blob content → extracted for shell stdin
- Metadata preserved through pipeline

---

## Command Naming Conventions

### Mining Metaphor
The `/mine` command family uses consistent mining imagery:

- **`cast`** - Casting ore down the mine shaft (uploading documents)
- **`dig`** - Digging up ore/insights (querying with AI)
- **`use`** - Switch which mine you're working (collection context)
- **`ls`** - List available mines (collections)
- **`init`** - Open a new mine (create collection)

**Why the change?**
- `upload` felt too technical/generic
- `query` was too long, didn't fit metaphor
- `cast` (4 chars) vs `upload` (6 chars) = shorter
- `dig` (3 chars) vs `query` (5 chars) = shorter
- Cohesive metaphor aids memorization

### Backward Compatibility
Old names still work as aliases:
- `/mine upload` → routes to `cast` handler
- `/mine query` → routes to `dig` handler

### Verb Selection Philosophy
1. **Short** - Typing efficiency matters
2. **Memorable** - Consistent metaphor
3. **Intuitive** - Action matches purpose
4. **Composable** - Works in pipes

---

## Configuration Files

### User Preferences (`~/.isaac/config.json`)
```json
{
  "user": {
    "name": "username",
    "email": "user@example.com"
  },
  "ai": {
    "enabled": true,
    "provider": "xai",
    "model": "grok-3"
  },
  "cloud": {
    "enabled": true,
    "sync_interval": 300
  },
  "xai": {
    "api_key": "xai-...",
    "api_url": "https://api.x.ai/v1",
    "collections": {
      "tc_logs": "uuid-here",
      "cpf_logs": "uuid-here"
    }
  }
}
```

### Tier Defaults (`isaac/data/tier_defaults.json`)
```json
{
  "1": ["ls", "cd", "pwd"],
  "2": ["grep", "head", "tail"],
  "3": ["cp", "mv", "git"],
  "4": ["rm", "format", "dd"]
}
```

---

## Testing Your Commands

### Manual Testing Workflow
```bash
# Test session memory
/ask what is docker?
/ask tell me more # Should remember previous context

# Test Collections
/mine ls
/mine use tc_logs
/mine dig "errors"
/mine cast ~/test.txt

# Test piping (after Phase 1)
ls | /save test.txt
cat test.txt | /analyze
/ask "hello" | /summarize short
```

### Automated Tests
```bash
# Run all tests
pytest tests/ --cov=isaac --cov-report=term

# Specific test suites
pytest tests/test_tier_validator.py -v
pytest tests/test_cloud_client.py -v
pytest tests/test_ai_integration.py -v
```

---

## Command Router Integration

### Classification Flow
```
User Input → Prefix Detection → Route to Handler
```

**Prefixes:**
- `/` = Meta-command or AI command (immediate routing)
- `isaac` = Natural language (translate to shell)
- None = Shell command (tier validation → execute)

### Execution Pipeline
```python
# Simplified router logic
if input.startswith('/'):
    if input.startswith('/ask'):
        return ask_handler(input)
    elif input.startswith('/mine'):
        return mine_handler(input)
    elif input.startswith('/save'):
        return save_handler(input)
    else:
        return meta_command_handler(input)
elif input.startswith('isaac '):
    query = input[6:].strip()
    translated = ai_translate(query)
    return execute_shell(translated)
else:
    tier = get_tier(input)
    if tier >= 3:
        return ai_validate_then_execute(input)
    else:
        return execute_shell(input)
```

---

## Cross-Platform Notes

### PowerShell vs Bash
Isaac adapts command suggestions based on detected shell:

**PowerShell (Windows):**
```powershell
Get-ChildItem | /save
Select-String "error" log.txt | /analyze
Measure-Object -Line file.txt
```

**Bash (Unix):**
```bash
ls | /save
grep "error" log.txt | /analyze
wc -l file.txt
```

### Unix Alias System (Phase 2)
Optional translation for Unix users on Windows:
```bash
# User types (Unix)
grep "error" log.txt

# Isaac translates (if command not found)
Select-String "error" log.txt

# With notification
[isaac: translated 'grep' → 'Select-String']
```

**Common Aliases:**
- `grep` → `Select-String`
- `find` → `Get-ChildItem -Recurse`
- `ps` → `Get-Process`
- `kill` → `Stop-Process`
- `cat` → `Get-Content`
- `ls` → `Get-ChildItem`
- `wc` → `Measure-Object`

---

## Implementation Status

### ✅ Complete (Working in Production)
- `/help`, `/status`, `/config`, `/clear`
- `/ask` with session memory
- `/mine cast` (was upload)
- `/mine dig` (was query)
- `/mine use`, `/mine ls`, `/mine init`
- Tier-based command validation
- Cloud sync for preferences/history

### 🚧 In Progress (Phase 1)
- PipeEngine module
- `/save` command
- `/analyze` command
- `/summarize` command
- Shell adapter stdin support
- Hybrid shell/Isaac piping

### 📋 Planned (Future Phases)
- **Phase 2:** Unix alias translation
- **Phase 3:** `/translate`, `/extract`, `/format`
- **Phase 4:** `/chart`, `/alert`, visualization tools
- Chain query in `/mine dig` (Collections → Chat)

---

## Quick Reference Cheat Sheet

### Most Common Commands
```bash
# AI Chat
/ask <question>              # Ask AI with memory

# Mining (Collections)
/mine cast <file>            # Upload to Collections
/mine dig <question>         # Search with AI
/mine use <name>             # Switch collection
/mine ls                     # List collections

# Piping (Phase 1)
<command> | /save <file>     # Save output
<command> | /analyze         # AI analysis
<command> | /summarize       # Condense text

# Hybrid Examples
ls | /save dir.txt
/ask "kubernetes" | /summarize short
/mine dig "errors" | grep "404" | wc -l
```

### Configuration
```bash
/config ai on                # Enable AI
/config cloud off            # Disable cloud sync
/status                      # Check system status
/help                        # Show help
```

---

## Learning Path

### Beginner (Week 1)
1. Master `/ask` for questions
2. Learn `/mine cast` and `/mine dig`
3. Use basic shell commands
4. Try `/status` and `/config`

### Intermediate (Week 2-3)
1. Explore piping: `ls | /save`
2. Chain AI commands: `/ask | /summarize`
3. Mix shell + Isaac: `/mine dig | grep`
4. Experiment with Collections

### Advanced (Week 4+)
1. Complex pipelines: multi-stage transformations
2. Custom Collections for different projects
3. Automation with Isaac commands
4. Integrate into daily workflow

---

## Getting Help

### Built-In Help
```bash
/help                        # General help
/help <command>              # Command-specific help
/mine help                   # Mining command guide
```

### Documentation Files
- `.claude/bible/ISAAC_PIPING_ARCHITECTURE.md` - System design
- `.claude/bible/ISAAC_FINAL_DESIGN.md` - Overall architecture
- `.claude/bible/ISAAC_COMMAND_REFERENCE.md` - This file

### Test Your Knowledge
After reading this guide, you should be able to:
- [ ] Explain the difference between `/ask` and `/mine`
- [ ] Write a hybrid pipe command (shell + Isaac)
- [ ] Upload files to Collections with `/mine cast`
- [ ] Search Collections with `/mine dig`
- [ ] Save command output with `/save`
- [ ] Use AI analysis with `/analyze`

---

**Next:** Start with `/ask` to test AI chat, then experiment with `/mine` for your documents. When Phase 1 launches, try piping commands together!
