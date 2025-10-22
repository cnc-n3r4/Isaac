# Isaac Command Structure - Authoritative Reference

**Date:** 2025-10-21  
**Status:** ✅ STANDARDIZED ACROSS ALL DOCUMENTATION

---

## The Rules (Crystal Clear!)

### 1. ALL Internal Commands Use `/` Slash Prefix

**Meta-Commands:**
- `/help` - Show available commands
- `/config` - Configuration management  
- `/status` - System status check
- `/ask <query>` - AI queries and command translation
- `/task <goal>` - Multi-step task planning
- `/collect <files>` - Upload to cloud collection
- `/debug <file>` - AI file analysis
- `/msg <message>` - Cloud messaging
- `/clear` - Clear screen
- `/exit`, `/quit` - Exit Isaac

### 2. Device Routing Uses `!` Bang Prefix

**Target specific devices:**
- `/msg !laptop2 "don't forget to copy that stuff"` - Send message to laptop2
- `/show-cmd !desktop3` - View command history from desktop3
- `/collect !homeserver` - Upload collection to specific device

**Pattern:** `/command !devicename <args>`

### 3. Natural Language Alternative

**Two ways to make AI queries:**

**Internal Mode (after `isaac /start`):**
- `/ask where is alaska?` - Standard, preferred syntax
- `isaac where is alaska?` - Also works (convenience)

**External Mode (before starting Isaac):**
- `isaac /ask where is alaska?` - External command format
- `isaac where is alaska?` - Direct query (shorthand)

---

## Mode-Specific Usage

### External Mode (Before `/start`)

From regular shell, use `isaac` prefix:
```bash
C:\> isaac /start              # Enter internal mode
C:\> isaac /ask <query>        # Quick AI query
C:\> isaac /task <goal>        # External task execution
C:\> isaac /msg !device "msg"  # Cloud message
```

### Internal Mode (After `isaac /start`)

Inside Isaac shell, use `/` commands directly:
```
$> /help                       # Show help
$> /config                     # Configuration
$> /ask where is alaska?       # AI query (standard)
$> isaac where is alaska?      # Also works (convenience)
$> /task backup my files       # Multi-step task
$> /msg !laptop2 "update"      # Message another device
$> /show-cmd !desktop3         # View other device history
$> /collect projectB           # Upload to collection
$> /exit                       # Return to external shell
```

### Regular Shell Commands (No Prefix)

Shell commands run directly with tier validation:
```
$> ls                          # Tier 1 - instant
$> grep pattern file.txt       # Tier 2 - auto-execute
$> rm important.txt            # Tier 3+ - AI validation
```

---

## Why This Structure?

### Clarity
- `/` immediately signals "this is an Isaac command"
- No ambiguity with shell commands
- Predictable, learnable pattern

### Consistency
- All meta-commands follow same pattern
- Device routing is distinct with `!` 
- Natural language is clearly optional

### Flexibility
- `isaac <query>` works everywhere (convenience)
- `/ask <query>` is standard in internal mode
- Clear external vs internal modes

---

## Examples from User Interaction Vision

```
# External Mode
C:\> isaac /start
[Isaac starts up]

# Internal Mode
$> ls
file1.txt
file2.txt

$> /ask what is the biggest city in illinois
Chicago is the largest city in Illinois...

$> pwf
Did you mean 'pwd'? 
/home/user/projects

$> /task backup my project files
[Planning...]
Step 1: Identify project files
Step 2: Create backup folder
Step 3: Copy files
[Execute? y/n]

$> /msg !laptop2 "don't forget to copy that stuff"
done. message queued on cloud.

$> /config
=== ISAAC Configuration ===
Version: 1.0.2
Session: 01cb3c
...

$> /exit
Isaac's outtie 5000! See ya!
C:\>
```

---

## Implementation Notes

### Command Router Logic

```python
# In isaac/core/command_router.py

def route_command(self, user_input: str):
    # Check for meta-commands first
    if user_input.startswith('/'):
        return self._handle_meta_command(user_input)
    
    # Check for natural language with isaac prefix
    if user_input.lower().startswith('isaac '):
        query = user_input[6:].strip()
        return self._handle_ai_query(query)
    
    # Regular shell command with tier validation
    return self._handle_shell_command(user_input)
```

### Meta-Command Handler

```python
def _handle_meta_command(self, command: str):
    parts = command[1:].split()  # Remove leading /
    cmd_name = parts[0].lower()
    args = parts[1:]
    
    # Check for device routing
    if args and args[0].startswith('!'):
        device = args[0][1:]  # Remove ! prefix
        return self._route_to_device(cmd_name, device, args[1:])
    
    # Route to appropriate command handler
    if cmd_name == 'help':
        from isaac.commands.help import HelpCommand
        return HelpCommand(self.session).execute(args)
    elif cmd_name == 'config':
        from isaac.commands.config import ConfigCommand
        return ConfigCommand(self.session).execute(args)
    # ... etc
```

---

## Documentation Status

✅ **copilot-instructions.md** - Updated with command structure
✅ **ISAAC_FINAL_DESIGN.md** - Command reference added
✅ **ISAAC_UI_SPECIFICATION.md** - Quick reference added
✅ **ISAAC_AI_INTERACTION_DESIGN.md** - Command structure section added
✅ **This file** - Authoritative reference created

---

**Remember:** `/` for commands, `!` for devices, `isaac <query>` optional everywhere!
