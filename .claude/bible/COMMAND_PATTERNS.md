# Isaac Command Patterns - Complete Reference

**Status:** ✅ AUTHORITATIVE  
**Purpose:** Crystal clear command structure with real interaction examples

---

## Command Structure Rules

### 1. External Mode (Before `isaac /start`)

**Syntax:** `isaac /command [args]`

**Available Commands:**
- `isaac /ask <query>` - AI query
- `isaac /move <files>` - File operations  
- `isaac /task <description>` - Multi-step tasks
- `isaac /start` - Enter internal mode
- `isaac /help` - Show help

**Restrictions:**
- Internal-only commands (`/f`, `/msg`, `/collect`, `/debug`) are BLOCKED
- Error message: "internal isaac command not authorized for external use"

### 2. Internal Mode (After `isaac /start`)

**Prompt:** `$>`

**All Internal Commands Use `/` Prefix:**
- `/help` - Show available commands
- `/config` - Configuration management
- `/status` - System status check
- `/ask <query>` - AI query
- `/task <description>` - Multi-step automation
- `/collect <path>` - Upload to cloud collections
- `/debug --file <file>` - AI debugging analysis
- `/f <cmd>` - Force execute (bypasses tier validation, INTERNAL-ONLY)
- `/msg !device "text"` - Message another device (uses `!` for routing)
- `/show-cmd !device` - View device command history
- `/clear` - Clear screen
- `/exit`, `/quit` - Exit internal mode

**Device Routing Uses `!` Prefix:**
- `/msg !laptop2 "text"` - Send to laptop2
- `/show-cmd !desktop3` - View desktop3's history

**Natural Language:**
- `isaac <query>` - Works same as `/ask <query>`
- Plain queries without 'isaac' → "I have a name, use it."

**Shell Commands:**
- No prefix: `ls`, `cd`, `rm` → Go through tier validation

---

## Real Interaction Examples

### External Mode Usage

```powershell
C:\> isaac /ask where is alaska?
up north (or whatever it responds)

C:\> isaac /move those files i was working on earlier all to the cloud
done! (and then whatever proof or validation would be appropriate)

C:\> isaac /start
[isaac starts in output window, takes over shell as interface]
```

### External Mode Errors

```powershell
C:\> isaac what is warmer california or florida?
type 'isaac /help' for help.
to make a general query, use 'isaac /ask'.

C:\> isaac /f rm C:\user\all-my-personal-stuff-folder
internal isaac command not authorized for external use.
type 'isaac /help' for help.
to use full isaac implementation use 'isaac /start' first.

C:\> isaac /ask what is warmer california or florida?
isaac> depends where, what time of year.. yada yada yada
```

### Internal Mode - Shell Commands

```powershell
$> ls
[lists files like normal]

$> where is alaska?
[system error because 'where' is a valid PowerShell command and that wasn't a valid input]
```

### Internal Mode - Natural Language

```powershell
$> isaac where is alaska?
[isaac response, no matter how short or long]

$> how many species of bird are there?
I have a name, use it.

$> isaac how many species of birds are there?
[isaac response, no matter how short or long]

$> /ask how many species of birds are there?
[isaac response, no matter how short or long. same as using 'isaac' internally]
```

### Internal Mode - Tier Validation

```powershell
$> rm C:\user\all-my-personal-stuff-folder
[level 3] do you really want to remove this? (y/n)
$> n
saved your dumbass

$> /f rm C:\user\all-my-personal-stuff-folder2
done!
```

### Internal Mode - Meta-Commands

```powershell
$> /config
[loads config stuff]

$> /collect the projectB folder
done. ProjectB folder uploaded to 'codingstuff' collection.
type /collect --help for more information on /collect command.

$> /debug --setpro "codingstuff"
done. Project folder to "codingstuff"

$> /debug --file "problemfile.py"
examining file "problemfile.py" in "codingstuff" collection.
will msg cloud when response is found.
```

### Internal Mode - Device Messaging

```powershell
$> /msg !laptop2 "dont forget to copy that stuff"
done. message queued on cloud. when you login from laptop2, you will get this message.
```

### Internal Mode - Contextual AI

```powershell
$> isaac have you had a chance to look at that problem file?
you mean that "problemfile.py" you uploaded last week? (y/n)
$> n
please clarify which file then.

$> the divorce stuff
I see the "all_the_money_i_lost_in_the_divorce.doc" was being used recently, that one? (y/n)
$> y
No. You did not upload it to "collections" or start a new "collection" for it.

$> oh ok
I have a name, use it.

$> isaac oh ok
thats better. If you like I can guide you, or direct you to the x.ai place to do this.
```

### Internal Mode - Edge Cases

```powershell
$> isaac /start
I am already started.

$> /exit
Isaac's outtie 5000 ! See ya!
```

---

## Key Design Principles

1. **All internal commands use `/` prefix** - Makes it clear when talking to Isaac vs shell
2. **Device routing uses `!` prefix** - Consistent syntax for cross-device operations
3. **Natural language needs 'isaac' prefix** - Or get sass: "I have a name, use it."
4. **External mode is restricted** - Safety first, internal-only commands blocked
5. **Personality in responses** - Sass for errors, playful confirmations, contextual awareness
6. **Force command is internal-only** - `/f` bypasses validation, too dangerous for external use

---

## Command Categories

### Meta-Commands (Configuration & Info)
- `/help`, `/config`, `/status`

### AI Interaction
- `/ask <query>`, `isaac <query>`

### File Operations  
- `/collect <path>`, `isaac /move <files>` (external)

### Task Automation
- `/task <description>`

### Debugging
- `/debug --file <file>`, `/debug --setpro <project>`

### Device Communication
- `/msg !device "text"`, `/show-cmd !device`

### Safety Override
- `/f <cmd>` (internal-only, bypasses tier validation)

### Shell Control
- `/clear`, `/exit`, `/quit`

---

## Implementation Notes

### Command Router Logic

```python
def route_command(user_input: str, mode: str):
    """
    Route command based on mode and prefix
    
    Args:
        user_input: Raw input from user
        mode: 'external' or 'internal'
    """
    # External mode
    if mode == 'external':
        if user_input.startswith('isaac /'):
            cmd = user_input[6:].strip()  # Remove 'isaac '
            if cmd.startswith('/'):
                cmd_name = cmd[1:].split()[0]
                if cmd_name in ['f', 'msg', 'collect', 'debug']:
                    return error("internal isaac command not authorized for external use")
                return execute_external_command(cmd)
        return error("type 'isaac /help' for help")
    
    # Internal mode  
    if mode == 'internal':
        if user_input.startswith('/'):
            return execute_internal_command(user_input)
        elif user_input.lower().startswith('isaac '):
            query = user_input[6:].strip()
            return ask_ai(query)
        elif is_shell_command(user_input):
            return execute_with_tier_validation(user_input)
        else:
            return sass("I have a name, use it.")
```

---

## Testing Checklist

- [ ] External mode blocks `/f`, `/msg`, `/collect`, `/debug`
- [ ] External mode allows `/ask`, `/start`, `/help`
- [ ] Internal mode accepts all `/commands`
- [ ] Device routing with `!` works correctly
- [ ] Natural language without 'isaac' gets sass response
- [ ] `isaac <query>` works in both modes
- [ ] Tier validation triggers on dangerous commands
- [ ] `/f` bypasses tier validation
- [ ] Personality responses show correctly
- [ ] Context awareness in AI responses
- [ ] `/exit` returns to external mode properly

---

**Last Updated:** 2025-10-21  
**Canonical Reference:** This document is the authoritative source for Isaac command patterns
