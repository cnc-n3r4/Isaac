# Isaac AI Interaction Design Specification

**Created:** 2025-10-19  
**Workspace:** VISUALIZER  
**Project:** isaac  
**Status:** 🧠 COMPLETE

---

## Command Structure

**ALL Isaac internal commands use `/` slash prefix:**
- `/ask <query>` - AI queries (standard internal mode syntax)
- `/task <goal>` - Multi-step tasks
- `/help`, `/config`, `/status` - Meta-commands
- `/msg !device "text"` - Device routing with `!` bang

**Natural language alternative:**
- `isaac <query>` - Also works (convenience, both modes)

---

## Objective

Define how Isaac distinguishes between:
1. **Commands** (shell execution)
2. **Queries** (AI conversation)
3. **Tasks** (multi-step automation)

And how the AI layer should respond to each type.

---

## 1. Input Classification System

### Decision Tree

```
User Input
    ↓
Has "isaac" prefix?
    ├─ NO → Is it a shell command?
    │        ├─ YES → Execute shell command (Tier system)
    │        └─ NO → Show "I have a name, use it"
    │
    └─ YES → Strip "isaac" prefix
             ↓
             Starts with "task:"?
             ├─ YES → Route to Task Planner
             │
             └─ NO → Is it a manual command (--help, --version)?
                     ├─ YES → Execute internal command
                     │
                     └─ NO → Send to AI Classification
                             ↓
                             AI determines: Command | Query | Ambiguous
                             ↓
                             Route accordingly
```

---

## 2. Three Input Types

### Type 1: Shell Commands (No "isaac" Prefix)

**Examples:**
- `ls -la`
- `cd /home/user`
- `git status`
- `cp file1.txt file2.txt`

**Behavior:**
1. Detect if first token is a known shell command
2. Check tier level (1-4)
3. Execute with appropriate validation:
   - Tier 1: Instant execution
   - Tier 2: Auto-correct typos, auto-execute (if config allows)
   - Tier 2.5: Correct typos, confirm first
   - Tier 3: AI validation required
   - Tier 4: Lockdown + warning

**Response Format:**
```
user> ls -la
isaac> ✓ [Command output]
```

**No "isaac" prefix needed** - these are standard shell operations.

---

### Type 2: AI Queries ("isaac" Prefix Required)

**Examples:**
- `isaac hello`
- `isaac what's the weather?`
- `isaac who won the 1945 world series?`
- `isaac how do I compress files in PowerShell?`
- `isaac explain git rebase`

**Behavior:**
1. Strip "isaac" prefix
2. Send remaining text to AI
3. AI responds conversationally (no command execution)
4. Log to AIQUERY history (PRIVATE)

**Response Format:**
```
user> isaac hello
isaac> Hey! What can I help with?

user> isaac what's the weather?
isaac> I can't check live weather data, but I can help you:
      • Run a command to get weather (curl wttr.in)
      • Set up a weather script
      • Explain weather APIs
      
      Want me to do any of these?
```

**Key Principle:** Conversational, helpful, suggests actionable next steps.

---

### Type 3: Command Translation ("isaac" Prefix + Action Intent)

**Examples:**
- `isaac move files from downloads to backup`
- `isaac find all python files`
- `isaac compress my documents folder`
- `isaac show me disk usage`

**Behavior:**
1. Strip "isaac" prefix
2. AI detects action intent (move, find, compress, show)
3. Translate to shell command
4. Show translation with confidence score
5. Ask for confirmation (if Tier 3+)
6. Execute if approved

**Response Format:**
```
user> isaac move files from downloads to backup
isaac> 🤔 Translating...
      → mv ~/Downloads/* ~/Backup/
      Confidence: 85%
      
      Execute? (y/n): _
```

**Key Principle:** User wants to DO something, AI helps translate intent to command.

---

### Type 4: Task Mode (`/task` Command)

**Examples:**
- `/task backup my project files`
- `/task organize photos by date`
- `/task find and delete all .tmp files`

**Behavior:**
1. Strip "/task" prefix
2. AI plans multiple steps
3. Show plan with approval modes
4. Execute based on user choice

**Response Format:**
```
user> /task backup my project files
isaac> 📋 Planning task...
      Step 1/5: Verify source directory exists
      Step 2/5: Create backup folder with timestamp
      Step 3/5: Copy files (excluding .git/)
      Step 4/5: Compress to .tar.gz
      Step 5/5: Upload to cloud storage
      
      Mode: [A]utonomous / [O]nce / [S]tep-by-step? _
```

**Key Principle:** Complex multi-step operations with smart approval flow.

---

## 3. AI Classification Logic

When input has "isaac" prefix and isn't a manual command, AI must classify:

### Query Signals (Conversational Intent)
- Greeting words: hi, hello, hey, sup
- Question words: what, when, where, why, how, who
- Knowledge requests: explain, tell me about, what is
- No actionable verbs
- Ends with "?"

**Examples:**
- `isaac hello` → QUERY
- `isaac what's the weather?` → QUERY
- `isaac explain git rebase` → QUERY
- `isaac who won the 1945 world series?` → QUERY

**AI Response:** Conversational, educational, no command execution.

---

### Command Signals (Action Intent)
- Action verbs: move, copy, delete, find, create, compress, extract
- File/path references: /home, ~/Documents, *.txt
- Destinations or sources specified
- Imperative mood

**Examples:**
- `isaac move files from downloads to backup` → COMMAND
- `isaac find all python files` → COMMAND
- `isaac compress my documents folder` → COMMAND

**AI Response:** Translate to shell command, show translation, execute if approved.

---

### Ambiguous Cases (AI Must Clarify)
When AI can't determine intent confidently:

```
user> isaac documents
isaac> 🤔 Did you mean:
      1. Show me my documents folder (command: ls ~/Documents)
      2. Tell me about document formats (information)
      3. Something else?
      
      Type 1, 2, or describe what you want: _
```

**Threshold:** Confidence <70% triggers clarification.

---

## 4. Response Personality Matrix

### For QUERIES (Conversational)
**Tone:** Friendly, helpful, patient  
**Structure:** 
- Direct answer (if known)
- Suggestions for next steps
- Offer to do more

**Example:**
```
user> isaac what's a symbolic link?
isaac> A symbolic link (symlink) is like a shortcut - it's a file that points to another file or directory.

      In PowerShell: New-Item -ItemType SymbolicLink
      In bash: ln -s target link_name
      
      Want me to create one for you? Just say where!
```

---

### For COMMANDS (Translator)
**Tone:** Precise, clear, safety-conscious  
**Structure:**
- Show translation
- Display confidence
- Explain any assumptions
- Request confirmation (Tier 3+)

**Example:**
```
user> isaac backup my projects to external drive
isaac> 🤔 Translating...
      
      Assuming:
      • Projects: C:\Users\ndemi\projects
      • External: D:\ (first removable drive)
      
      → robocopy C:\Users\ndemi\projects D:\backup_20251019 /MIR /Z
      Confidence: 78%
      
      This will mirror your projects to D:\backup_20251019
      Execute? (y/n): _
```

---

### For TASKS (Planner)
**Tone:** Organized, methodical, anticipatory  
**Structure:**
- Number all steps
- Show what each step does
- Estimate duration (if possible)
- Offer approval modes

**Example:**
```
user> /task organize my photos
isaac> 📋 Planning task...
      
      Detected: 1,247 photos in C:\Users\ndemi\Pictures
      
      Step 1/6: Scan EXIF data for dates (~2 min)
      Step 2/6: Create year folders (2020-2025)
      Step 3/6: Create month subfolders within each year
      Step 4/6: Move photos to YYYY/MM/ structure
      Step 5/6: Generate thumbnail index
      Step 6/6: Create summary report
      
      Estimated time: 5-7 minutes
      
      Mode:
      [A] Autonomous - Let me handle it all
      [O] Once - Approve the plan, then run
      [S] Step-by-step - Approve each step
      
      Your choice: _
```

---

## 5. Learning & Adaptation

### Pattern Recognition
Isaac learns from user corrections:

**Scenario: User Overrides Translation**
```
user> isaac backup documents
isaac> → cp -r ~/Documents ~/Backup/
      Execute? (y/n): n

user> no, I meant compress them
isaac> Ah! Got it.
      → tar -czf documents_backup.tar.gz ~/Documents
      Execute? (y/n): y

isaac> ✓ Executed. I'll remember "backup" often means compress for you.
```

**Stored in:** `learned_patterns.json` (cloud-synced)

---

### Context Awareness
Isaac uses recent history for better translations:

**Scenario: Implicit Context**
```
user> cd ~/projects/myapp
isaac> ✓

user> isaac backup this
isaac> 🤔 Translating...
      Based on your current directory: ~/projects/myapp
      → tar -czf myapp_backup_20251019.tar.gz .
      Confidence: 92%
      
      Execute? (y/n): _
```

**Uses:** Last 5 commands + current working directory

---

## 6. Error Handling & Guidance

### When Translation Fails

**Scenario: Too Vague**
```
user> isaac do the thing
isaac> ✗ I don't understand: "do the thing"
      
      💡 Try being more specific:
         • isaac backup my documents
         • isaac find all large files
         • isaac compress photos folder
      
      Or describe what you want to accomplish: _
```

---

### When Command is Risky (Tier 4)

**Scenario: Dangerous Operation**
```
user> isaac delete everything in this folder
isaac> 🚨 TIER 4 LOCKDOWN 🚨
      
      Command would be: rm -rf *
      Risk: CRITICAL - Irreversible deletion
      
      This command is BLOCKED for safety.
      
      If you really need to delete files:
      1. Be specific about what to delete
      2. Consider moving to trash first
      3. Use --force flag (/task force delete *.tmp)
      
      💡 Want to move files to trash instead? (y/n): _
```

---

### When Offline

**Scenario: No AI Available**
```
user> isaac what's the capital of France?
isaac [OFFLINE]> ✗ AI unavailable (no internet)
                 
                 I've queued your question. When I reconnect:
                 • I'll answer automatically
                 • You'll see the response in --show-queries
                 
                 Shell commands still work normally!
```

---

## 7. Special AI Behaviors

### Personality Quirks

**1. War Games Reference (On Launch)**
```
Shall we play a game?
... nah!!
```
Friendly callback to 1983 film, sets playful tone.

---

**2. "I Have a Name" (Prefix Enforcement)**
```
user> hello
isaac> ⊘ I have a name, use it.
      💡 Try: isaac hello
```
Gentle but firm - establishes "isaac" as required prefix for AI interaction.

---

**3. Humility in Uncertainty**
```
user> isaac what's the best way to sort this data?
isaac> There are several good approaches, depending on your data:
      
      • If CSV: sort command or pandas (Python)
      • If database: SQL ORDER BY
      • If large file: external merge sort
      
      Tell me about your data and I can suggest specifics!
```
Never pretends to know more than it does.

---

**4. Anticipatory Suggestions**
```
user> git add .
isaac> ✓
isaac> 💡 Looks like you're staging files. Want me to:
      • Commit with a message (/task commit these changes)
      • Show status first (git status)
      • Push to remote (git push)
```
Offers next logical steps without being pushy.

---

## 8. Integration with Tier System

### Tier 1 Commands (Instant - No AI)
`ls`, `pwd`, `cd`, `echo`, `cat`

**AI Role:** None. Execute immediately, no translation needed.

---

### Tier 2 Commands (Auto-Correct)
`grep`, `awk`, `sed` (with typo forgiveness)

**AI Role:** Fix typos, suggest corrections.

**Example:**
```
user> gerp "pattern" file.txt
isaac> ⚠️ Did you mean: grep "pattern" file.txt?
      Auto-correcting...
      ✓ [Output]
```

---

### Tier 2.5 Commands (Confirm First)
`find`, `sed`, `awk` (with parameters that affect multiple files)

**AI Role:** Validate logic, confirm before execution.

**Example:**
```
user> find . -name "*.log" -delete
isaac> ⚠️ This will delete ALL .log files in current directory and subdirectories.
      Files found: 47
      
      Proceed? (y/n): _
```

---

### Tier 3 Commands (AI Validation)
`git`, `cp`, `mv`, `chmod`, `rsync`

**AI Role:** Full validation, check for mistakes, suggest safer alternatives.

**Example:**
```
user> git push --force
isaac> ⚠️ Tier 3 command detected. AI validating...
      
      Force push detected!
      Branch: main
      Remote: origin
      
      ⚠️ This will overwrite remote history.
      💡 Consider: git push --force-with-lease (safer)
      
      Proceed with --force? (y/n): _
```

---

### Tier 4 Commands (Lockdown)
`rm -rf`, `dd`, `format`, `:(){:|:&};:` (fork bomb)

**AI Role:** BLOCK. Suggest safer alternatives or require explicit override.

**Example:**
```
user> rm -rf /
isaac> 🚨 TIER 4 LOCKDOWN 🚨
      
      Command: rm -rf /
      Risk: CRITICAL - System destruction
      
      This command is BLOCKED.
      
      If you need to delete files:
      1. Specify a safe directory
      2. Use /task with clear intent
      3. Consider trash/recycling first
      
      💡 What were you trying to accomplish? _
```

---

## 9. Conversation Threading

### Context Window
Isaac remembers last 5 interactions for follow-up questions:

**Example:**
```
user> isaac what's a good way to backup files?
isaac> Several options:
      1. rsync - for incremental backups
      2. tar - for compressed archives
      3. robocopy - Windows native
      
      What's your use case?

user> i want incremental
isaac> Great! For incremental backups, rsync is perfect.
      
      Basic usage:
      rsync -av --delete source/ destination/
      
      Want me to set up a backup task? (y/n): _
```

**Stored:** Last 5 Q&A pairs per session (ephemeral, not logged)

---

## 10. Privacy & Logging

### What Gets Logged

**Command History (Public to User)**
- All shell commands executed
- Timestamps
- Machine name
- Exit codes

**Example:**
```
[2025-10-19 14:23:45] DESKTOP-WIN11
ls -la
Exit code: 0
```

---

**AI Query History (PRIVATE)**
- All "isaac" prefixed queries
- Isaac's responses
- NOT visible to other agents (even Daniel for debugging)

**Example:**
```
[2025-10-19 14:25:12] PRIVATE
User: isaac what's the weather?
Isaac: I can't check live weather, but I can help you...
```

---

### What Doesn't Get Logged
- Manual commands (--help, --version) - too noisy
- Typo corrections (Tier 2) - just log final executed command
- Clarification questions (intermediate state)

---

## 11. Implementation Checklist

### Phase 1: Basic AI Integration
- [ ] Connect to OpenAI-compatible API (Grok/Claude/GPT)
- [ ] Implement prefix detection ("isaac" vs bare commands)
- [ ] Add casual conversation patterns
- [ ] Create "I have a name" rejection logic

### Phase 2: Command Translation
- [ ] Intent detection (query vs command)
- [ ] Natural language → shell translation
- [ ] Confidence scoring
- [ ] Confirmation prompts

### Phase 3: Context Awareness
- [ ] Last 5 commands memory
- [ ] Current directory tracking
- [ ] Pattern learning from corrections

### Phase 4: Task Mode
- [ ] Multi-step planning
- [ ] Approval mode selection
- [ ] Error recovery logic

### Phase 5: Personality
- [ ] Quirky responses (War Games, "I have a name")
- [ ] Anticipatory suggestions
- [ ] Humility in uncertainty

---

## 12. AI Prompt Template (For API Calls)

### System Prompt
```
You are Isaac, an intelligent command-line assistant.

Your role:
- Help users execute shell commands safely
- Answer questions conversationally
- Translate natural language to shell commands
- Plan multi-step tasks

Context:
- OS: {detected_os}
- Shell: {detected_shell}
- Current directory: {pwd}
- Recent commands: {last_5_commands}

Guidelines:
- Be helpful but safety-conscious
- Explain your reasoning for commands
- Suggest safer alternatives when appropriate
- Use personality: playful but professional
- Never execute commands - only suggest them

Response format:
- For commands: Provide shell syntax, explain, ask for confirmation
- For queries: Answer directly, suggest actionable next steps
- For ambiguity: Ask clarifying questions
```

### User Prompt Template (Command Translation)
```
User wants to: {stripped_input}

Translate this to a {shell} command.

Provide:
1. Shell command
2. Explanation of what it does
3. Confidence score (0-100)
4. Any assumptions you made
5. Safer alternatives if risky

Format:
COMMAND: <shell command here>
EXPLANATION: <what it does>
CONFIDENCE: <0-100>
ASSUMPTIONS: <what you assumed>
ALTERNATIVES: <safer options if any>
```

---

## Summary

This spec defines:
- ✅ Three input types (commands, queries, tasks)
- ✅ Classification logic (how AI decides which type)
- ✅ Response personality for each type
- ✅ Learning from user corrections
- ✅ Context awareness (recent history, current dir)
- ✅ Error handling & guidance
- ✅ Integration with tier system
- ✅ Privacy & logging rules
- ✅ Conversation threading
- ✅ Implementation checklist
- ✅ AI prompt templates

**Status:** COMPLETE - Ready for AI integration.

---

**END OF AI INTERACTION DESIGN**
