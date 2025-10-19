# Implementation: REPL Integration

## Goal
Integrate interactive REPL loop into __main__.py for continuous command execution.

**Time Estimate:** 60 minutes

---

## Architecture Reminder

**Purpose:** Provide interactive command-line interface
- Enter REPL when no CLI arguments provided
- Display simple `isaac>` prompt
- Execute commands via CommandRouter
- Handle exit conditions gracefully
- Maintain session state across commands

**User expects:**
```bash
PS C:\Projects\Isaac-1> isaac
Isaac > Ready.
isaac> backup my-folder
AI: Translating... → /home/user/my-folder
Destination: /mnt/external
Execute? (y/n) y
✓ Backup complete
isaac> list history
Command History:
✓ backup my-folder [2025-10-19 14:32]
isaac> exit
Isaac > Goodbye.
```

---

## File to Modify

**Path:** `isaac/__main__.py`

**Current State** (from DEBUG patch):
```python
import sys
from isaac.core.session_manager import SessionManager

def main():
    """Main entry point."""
    session = SessionManager()
    session.load_from_local()
    session.load_from_cloud()
    print("Isaac > Ready.")
    
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        print(f"Isaac > Executing: {command}")
        session._log_command(command)
        # TODO: Add actual command execution logic here
    else:
        # TODO: Implement REPL loop
        pass

if __name__ == "__main__":
    main()
```

---

## Complete Implementation

**Find (entire file):**
```python
import sys
from isaac.core.session_manager import SessionManager

def main():
    """Main entry point."""
    session = SessionManager()
    session.load_from_local()
    session.load_from_cloud()
    print("Isaac > Ready.")
    
    if len(sys.argv) > 1:
        command = ' '.join(sys.argv[1:])
        print(f"Isaac > Executing: {command}")
        session._log_command(command)
        # TODO: Add actual command execution logic here
    else:
        # TODO: Implement REPL loop
        pass

if __name__ == "__main__":
    main()
```

**Replace with:**
```python
"""
Isaac - AI-Enhanced Command-Line Assistant

Entry point for both CLI and interactive REPL modes.
"""

import sys
from isaac.core.session_manager import SessionManager
from isaac.core.command_router import create_router


def main():
    """
    Main entry point.
    
    Modes:
    - CLI: isaac <command> <args>  (executes and exits)
    - REPL: isaac  (enters interactive loop)
    """
    # Initialize session
    session = SessionManager()
    session.load_from_local()
    session.load_from_cloud()
    
    # Create command router
    router = create_router(session)
    
    print("Isaac > Ready.")
    
    # Determine mode based on arguments
    if len(sys.argv) > 1:
        # CLI mode - execute single command and exit
        command = ' '.join(sys.argv[1:])
        result = router.execute(command)
        print(result)
        
        # Exit with appropriate status code
        sys.exit(0 if result.success else 1)
    else:
        # REPL mode - interactive loop
        repl_loop(router)


def repl_loop(router):
    """
    Interactive REPL (Read-Eval-Print Loop).
    
    Continuously reads commands, executes them, and displays results
    until user exits.
    
    Args:
        router: CommandRouter instance for command execution
    """
    print("Type 'exit' or 'quit' to exit. Type 'help' for commands.\n")
    
    while True:
        try:
            # Display prompt and read input
            user_input = input("isaac> ").strip()
            
            # Skip empty input
            if not user_input:
                continue
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Isaac > Goodbye.")
                break
            
            # Execute command
            result = router.execute(user_input)
            
            # Display result
            print(result)
            print()  # Blank line for readability
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\n\nIsaac > Use 'exit' to quit.")
            print()
            continue
            
        except EOFError:
            # Handle Ctrl+D or end of input
            print("\n\nIsaac > Goodbye.")
            break
            
        except Exception as e:
            # Catch-all for unexpected errors
            print(f"\n✗ Unexpected error: {str(e)}")
            print("   💡 Please report this issue if it persists\n")
            continue


if __name__ == "__main__":
    main()
```

---

## Verification Steps

After implementation, verify:

- [ ] File modified at `isaac/__main__.py`
- [ ] No syntax errors on import
- [ ] CLI mode works: `python -m isaac backup test` executes command and exits
- [ ] REPL mode works: `python -m isaac` enters interactive loop
- [ ] Exit commands work: `exit`, `quit`, `q` all exit gracefully
- [ ] Ctrl+C doesn't crash: Prints message and continues REPL
- [ ] Ctrl+D exits cleanly
- [ ] Empty input ignored (doesn't crash)
- [ ] Results displayed with proper formatting

## Test Manually

### Test CLI Mode:
```bash
# From project root
python -m isaac --help
# Expected: Help text displayed, exits

python -m isaac --version
# Expected: Version displayed, exits

python -m isaac backup test to /tmp
# Expected: Executes backup (or prompts), exits
```

### Test REPL Mode:
```bash
# From project root
python -m isaac
# Expected: "Isaac > Ready." and "isaac>" prompt

# In REPL:
isaac> help
# Expected: Help text

isaac> list history
# Expected: Command history

isaac> exit
# Expected: "Isaac > Goodbye." and exits
```

### Test Error Handling:
```bash
# In REPL:
isaac> [press Ctrl+C]
# Expected: Message about using 'exit', continues REPL

isaac> [press Ctrl+D]
# Expected: "Goodbye" and exits

isaac> [press Enter on empty line]
# Expected: Ignores, shows new prompt
```

---

## Common Pitfalls

- ⚠️ **Exit status codes** - CLI mode should exit with 0 on success, 1 on failure. Use `sys.exit()`.

- ⚠️ **Ctrl+C handling** - Use `KeyboardInterrupt` exception to catch Ctrl+C. Don't let it crash the REPL.

- ⚠️ **Ctrl+D handling** - Use `EOFError` exception to catch Ctrl+D/end-of-input.

- ⚠️ **Empty input** - Check for empty strings after `.strip()` to avoid unnecessary command execution.

- ⚠️ **Router instantiation** - Create router once and reuse in REPL loop. Don't recreate on every command.

- ⚠️ **Blank lines** - Add blank line after each result for readability in REPL mode.

- ⚠️ **Import location** - Import `create_router` from `isaac.core.command_router`, not `CommandRouter` class directly.

---

## Integration Notes

**Exit Commands:**
- `exit`
- `quit`
- `q`
- All case-insensitive

**Prompt Format:**
- Simple: `isaac>`
- No path-awareness
- No timestamps
- Clean and consistent

**Result Display:**
- CommandResult has `__str__()` method
- Automatically formats status symbol + message
- Includes suggestion if present

**Error Resilience:**
- Catches `KeyboardInterrupt` (Ctrl+C)
- Catches `EOFError` (Ctrl+D)
- Catches general `Exception` as fallback
- All errors allow REPL to continue (except exit conditions)

---

**END OF IMPLEMENTATION**
