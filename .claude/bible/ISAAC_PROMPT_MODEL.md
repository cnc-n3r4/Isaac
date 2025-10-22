# Isaac Prompt Model - Authoritative Specification

**Last Updated:** October 22, 2025  
**Status:** AUTHORITATIVE - All documentation must follow this model

---

## Critical Clarification

**Isaac is a traditional shell interface, NOT a conversational chatbot.**

### The Correct Model

Isaac operates like a **normal terminal** where:
- User sees a **single prompt** (`$>` or their native shell prompt)
- Commands execute and output appears **without prefix**
- Prompt returns for next command
- Isaac operates **invisibly** in the middle, intercepting and routing commands

### Visual Examples

**Correct UI:**
```bash
$> /ask where is tallahassee?
Tallahassee is the capital city of Florida, located in the northern part of the state...
$> ls | /save dir.txt
Saved 150 bytes to dir.txt
$> python news.py | /mine cast news_cache
Cast into mine: 40 articles → news_cache collection
$>
```

**WRONG UI (Do NOT implement this):**
```bash
user> /ask where is tallahassee?     ❌ WRONG
isaac> Tallahassee is the capital... ❌ WRONG
user> ls | /save dir.txt             ❌ WRONG
isaac> Saved 150 bytes...            ❌ WRONG
```

---

## Architecture

### How It Works

```
┌─────────────────────────────────────────────┐
│  User's Terminal                             │
│                                              │
│  $> /ask "question"        ← User types      │
│  AI response here...       ← System output   │
│  $>                        ← Prompt returns  │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │  Isaac Layer (invisible)           │     │
│  │  ├─ Command Router                 │     │
│  │  ├─ Tier Validator                 │     │
│  │  ├─ AI Integration                 │     │
│  │  ├─ Pipe Engine                    │     │
│  │  └─ Shell Adapter                  │     │
│  └────────────────────────────────────┘     │
│                                              │
│  ┌────────────────────────────────────┐     │
│  │  Native Shell (PowerShell/bash)    │     │
│  └────────────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

### Command Flow

1. **User types at prompt:** `$> /ask "question"`
2. **Isaac intercepts:** Routes to AI handler
3. **AI responds:** Output printed directly
4. **Prompt returns:** `$>` ready for next command

No `isaac>` prefix on output. No `user>` prefix on input. Just a normal shell experience.

---

## Prompt Notation in Documentation

### For Code Examples

**When showing interactive sessions, use `$>` to indicate the prompt:**

```bash
$> /mine cast report.pdf
Cast into mine: report.pdf → default collection
$> /mine dig "what was in the report?"
The report discusses quarterly earnings with focus on...
$> ls | /save files.txt
Saved 245 bytes to files.txt
$>
```

**Output has NO prefix - it's just system response.**

### For Command-Only Examples

**When showing just the command (not interactive session), omit the prompt:**

```bash
# Good - just the command
/ask "what is kubernetes?"
python script.py | /mine cast | /save

# Also good - with prompt for context
$> /ask "what is kubernetes?"
$> python script.py | /mine cast | /save
```

### For Multi-Line Scripts

**Shell scripts or aliases don't need prompts:**

```bash
#!/bin/bash
# news-digest.sh
python news_fetch.py |
  /mine cast news_cache |
  /mine dig "summarize top 5 stories" |
  /save ~/news/digest.md
```

---

## Comparison with Other Tools

### Like These (Traditional Shell)

**Git:**
```bash
$ git status
On branch main...
$ git commit -m "fix"
[main abc123] fix
$
```

**Conda:**
```bash
(base) $ python --version
Python 3.11.0
(base) $ conda activate myenv
(myenv) $
```

**Docker:**
```bash
$ docker ps
CONTAINER ID   IMAGE...
abc123         nginx...
$
```

### NOT Like These (Conversational UI)

**ChatGPT CLI (hypothetical):**
```bash
You: what is kubernetes?           ❌ NOT THIS
ChatGPT: Kubernetes is...          ❌ NOT THIS
You: tell me more                  ❌ NOT THIS
```

**REPL (Python/Node):**
```python
>>> print("hello")                 ❌ NOT THIS
hello
>>> 
```

Isaac is **shell-first**, not chat-first.

---

## UI Elements

### The Prompt

**Default:** `$>` (simple, universal)

**Can be customized** to show:
- Current directory
- Git branch
- Cloud sync status
- AI enabled/disabled

**Example custom prompts:**
```bash
$>                                  # Minimal
[isaac] $>                          # Branded
C:\Projects\Isaac>                  # Directory
isaac@desktop:~/projects$           # Unix-style
[☁️ online] $>                      # Status indicator
```

### System Messages

**Status messages appear inline, not prefixed:**

```bash
$> /config cloud on
Cloud sync enabled.
$> /ask "test"
⚠️ AI request timeout. Retrying...
AI is a powerful technology...
$>
```

**NOT like this:**
```bash
$> /config cloud on
isaac> Cloud sync enabled.          ❌ WRONG
```

### Error Messages

**Errors appear inline:**

```bash
$> /mine dig "test"
Error: Collection 'default' not found. Use /mine init to create.
$> /ask
Error: /ask requires a question. Usage: /ask <question>
$>
```

### AI Thinking Indicators

**Show progress inline during long operations:**

```bash
$> /mine dig "complex query about many documents"
🔍 Searching collections... (3 found)
🤔 Analyzing results with AI...
Based on your documents, the answer is...
$>
```

**NOT as a conversation:**
```bash
user> /mine dig "query"             ❌ WRONG
isaac> 🔍 Searching...              ❌ WRONG
isaac> Based on your documents...   ❌ WRONG
```

---

## Implementation Guidelines

### For Coding Agents

**When implementing Isaac's UI:**

1. **Use native shell prompt** - Don't create custom prompt UI
2. **Print output directly** - No `isaac>` prefix
3. **Return to prompt** - Let shell handle prompt display
4. **Status in header** - Use fixed header for persistent status (optional)
5. **Inline indicators** - Show progress/errors as normal output

### Terminal Control

**Isaac CAN have a fixed header** showing status (optional):

```
┌─────────────────────────────────────────────────┐
│ ISAAC v2.0.0 │ Cloud: ☁️  │ AI: 🤖 │ Tier: 2    │
├─────────────────────────────────────────────────┤
│                                                  │
│  $> /ask "what is kubernetes?"                  │
│  Kubernetes is a container orchestration...     │
│  $> ls | /save files.txt                        │
│  Saved 245 bytes to files.txt                   │
│  $>                                              │
│                                                  │
└─────────────────────────────────────────────────┘
```

But the **main interaction area** is still traditional shell I/O.

### Code Example

```python
# In permanent_shell.py
def run_loop(self):
    while True:
        # Show prompt (can be custom or native)
        user_input = input("$> ")
        
        # Route command through Isaac
        result = self.command_router.route(user_input)
        
        # Print output directly (no prefix)
        if result.output:
            print(result.output)
        
        # Prompt automatically appears on next loop iteration
```

**NOT like this:**
```python
# WRONG IMPLEMENTATION
def run_loop(self):
    while True:
        user_input = input("user> ")        # ❌ WRONG
        result = self.route(user_input)
        print(f"isaac> {result.output}")    # ❌ WRONG
```

---

## Special Cases

### Task Mode

**Multi-step tasks still use single prompt:**

```bash
$> /task: create backup of all logs
📋 Planning task...
  Step 1: Find log files
  Step 2: Create archive
  Step 3: Upload to cloud
Execute? (y/n): y
✓ Step 1/3: Found 42 log files
✓ Step 2/3: Created backup.tar.gz (15.2 MB)
✓ Step 3/3: Uploaded to cloud
Task complete!
$>
```

### AI Confirmation Prompts

**Use inline prompts, not conversation format:**

```bash
$> rm -rf /important/data
⚠️ TIER 4 COMMAND - High Risk
This will permanently delete: /important/data (2.3 GB, 1,247 files)
Confirm? (yes/no): no
Aborted.
$>
```

### Natural Language Queries

**Even AI queries use shell format:**

```bash
$> isaac list all python files
🤔 Translating to shell command...
Executing: ls -la | grep ".py"
file1.py
file2.py
test_script.py
$>
```

---

## Documentation Standards

### All Future Docs Must Follow This Format

✅ **Correct:**
```bash
$> /ask "question"
Answer here...
$> /mine cast file.pdf
Cast into mine: file.pdf → collection
$>
```

❌ **Incorrect:**
```bash
user> /ask "question"
isaac> Answer here...
user> /mine cast file.pdf
isaac> Cast into mine...
```

### Exception: Design Documents

**When discussing the system abstractly, you can use labels:**

```
USER → COMMAND ROUTER → VALIDATOR → EXECUTOR → OUTPUT
```

But in **code examples** and **user-facing documentation**, always use the `$>` prompt model.

---

## Why This Matters

### For Users
- **Familiar** - Works like every other CLI tool
- **Transferable** - Shell knowledge applies directly
- **Efficient** - No extra typing/reading of prefixes
- **Professional** - Looks like production tooling

### For Developers
- **Simple** - Standard stdin/stdout model
- **Compatible** - Works with existing shell features
- **Debuggable** - Easy to trace I/O
- **Testable** - Standard CLI testing patterns work

### For Documentation
- **Clear** - No ambiguity about interaction model
- **Consistent** - All examples follow same pattern
- **Accurate** - Matches actual implementation

---

## Quick Reference

### DO ✅
- Use `$>` for prompt in examples
- Print output without prefix
- Show inline status/errors
- Follow shell conventions

### DON'T ❌
- Use `user>` or `isaac>` prompts
- Prefix output with `isaac>`
- Create conversational UI
- Deviate from shell model

---

## Update Checklist

All documentation must be updated to follow this model:

- [ ] ISAAC_COMMAND_REFERENCE.md
- [ ] ISAAC_PIPING_ARCHITECTURE.md
- [ ] ISAAC_UI_SPECIFICATION.md (major rewrite needed)
- [ ] ISAAC_FINAL_DESIGN.md
- [ ] piping_system_phase1.md
- [ ] unix_aliases_phase2.md
- [ ] command_aliases_phase4.md
- [ ] PIPING_SYSTEM_READY.md
- [ ] All implementation guides

**This is CRITICAL** - incorrect prompt notation will confuse every coding agent and result in wrong implementation.

---

**Next Action:** Systematically update all documentation files to use `$>` prompt model.
