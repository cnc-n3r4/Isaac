# Command Execution Framework - Implementation Instructions

## 📦 Package Overview

**Feature:** Complete command execution framework for Isaac CLI

**Components:**
- Command router and parser
- Backup/restore/list/help handlers  
- Interactive REPL loop
- AI translation layer (placeholder for Phase 3)

**Estimated Time:** 6-8 hours

---

## 📂 File Structure

```
isaac/
├── __main__.py (MODIFY)
├── core/
│   ├── command_router.py (CREATE)
│   └── ai_translator.py (CREATE)
└── commands/
    ├── __init__.py (CREATE)
    ├── backup.py (CREATE)
    ├── restore.py (CREATE)
    ├── list.py (CREATE)
    └── help.py (CREATE)
```

---

## 🎯 Execution Order

**CRITICAL:** Execute files in this exact order per `00_run_order.yaml`

1. **Read:** `01_feature_brief.md` - Context and architecture
2. **Implement:** `02_command_router_impl.md` - Core router
3. **Implement:** `03_backup_handler_impl.md` - Backup handler
4. **Implement:** `04_restore_handler_impl.md` - Restore handler
5. **Implement:** `05_list_handler_impl.md` - List handler
6. **Implement:** `06_help_handler_impl.md` - Help handler
7. **Implement:** `07_repl_integration_impl.md` - REPL loop (modifies __main__.py)
8. **Implement:** `08_ai_translation_impl.md` - AI translator (placeholder)
9. **Document:** `XX_COMPLETION_REPORT.md` - Fill out after completion

---

## ✅ Verification Checkpoints

### After Step 2 (Command Router)
```python
from isaac.core.command_router import CommandRouter
from isaac.core.session_manager import SessionManager

session = SessionManager()
router = CommandRouter(session)
cmd_type, tokens = router.parse("--help")
assert cmd_type.name == "INTERNAL"
print("✓ CommandRouter working")
```

### After Step 6 (All Handlers)
```python
from isaac.commands import backup, restore, list, help
print("✓ All handlers importable")
```

### After Step 7 (REPL Integration)
```bash
python -m isaac --help
# Should display help and exit

python -m isaac
# Should enter REPL with isaac> prompt
```

### After Step 8 (AI Translation)
```python
from isaac.core.ai_translator import create_translator
translator = create_translator()
result = translator.translate("backup my documents")
assert result is not None
print("✓ AI translator working (placeholder)")
```

---

## 🧪 Final Testing

### CLI Mode Tests
```bash
# Help
python -m isaac --help
python -m isaac --version

# Commands
python -m isaac backup test-folder to /tmp
python -m isaac list history
```

### REPL Mode Tests
```bash
python -m isaac
```
Then in REPL:
```
isaac> help
isaac> backup test-folder to /tmp
isaac> list history
isaac> exit
```

### Error Handling Tests
In REPL:
- Press Ctrl+C (should display message, continue)
- Press Ctrl+D (should exit cleanly)
- Type empty line (should ignore)
- Type invalid command (should show suggestion)

---

## 📝 Commands Package Init

Create `isaac/commands/__init__.py`:

```python
"""
Isaac command handlers package.

Handlers:
- backup: Backup files/folders
- restore: Restore from backups
- list: List history and backups
- help: Command reference
"""

from isaac.commands.backup import BackupHandler
from isaac.commands.restore import RestoreHandler
from isaac.commands.list import ListHandler
from isaac.commands.help import HelpHandler

__all__ = [
    'BackupHandler',
    'RestoreHandler',
    'ListHandler',
    'HelpHandler',
]
```

---

## 🐛 Common Issues & Solutions

### Import Errors
**Problem:** `ModuleNotFoundError: No module named 'isaac.commands'`  
**Solution:** Ensure `isaac/commands/__init__.py` exists (see above)

### Circular Import
**Problem:** Circular import between router and handlers  
**Solution:** Handlers are imported lazily inside router methods (already implemented)

### REPL Not Exiting
**Problem:** `exit` command doesn't work  
**Solution:** Check case-insensitive comparison: `user_input.lower() in ['exit', 'quit', 'q']`

### Path Resolution Fails
**Problem:** "my documents" doesn't resolve  
**Solution:** Ensure path exists on system. AITranslator only returns paths that exist.

### Ctrl+C Crashes REPL
**Problem:** REPL exits on Ctrl+C  
**Solution:** Ensure `KeyboardInterrupt` exception is caught in repl_loop()

---

## 📊 Success Metrics

**Must Pass:**
- [ ] All files created without syntax errors
- [ ] CommandRouter parses all command types
- [ ] CLI mode executes commands and exits
- [ ] REPL mode provides interactive loop
- [ ] All handlers execute without errors
- [ ] Help system displays ≤30 lines
- [ ] Error handling prevents crashes
- [ ] Status symbols display correctly (✓/✗/⊘)

**Quality Indicators:**
- [ ] Code follows existing Isaac patterns
- [ ] Docstrings on all classes and methods
- [ ] Type hints on function signatures
- [ ] Helpful error messages with suggestions
- [ ] Consistent formatting and style

---

## 🚀 After Implementation

### 1. Fill Out Completion Report
Complete `XX_COMPLETION_REPORT.md` with:
- Actual time spent
- Issues encountered
- Test results
- Statistics
- Notes for Phase 3

### 2. Save Report
```
C:\Users\ndemi\Desktop\Claude\handoffs\isaac\from-agent\
    command-execution-framework\COMPLETION_REPORT.md
```

### 3. Update Project Status
Log completion to tracker workspace:
```
C:\Users\ndemi\Desktop\Claude\handoffs\isaac\to_tracker\
    command_execution_framework_complete.md
```

---

## 🔗 Related Work

**Dependencies:**
- Existing SessionManager (C:\Projects\isaac-1\isaac\core\session_manager.py)
- Python standard library (shlex, pathlib, dataclasses)

**Follow-up Work:**
- Phase 3: AI Integration (see mailbox: phase3_ai_integration_yaml_request.md)
- SessionManager enhancements (history storage, backup tracking)
- Shell command execution integration

---

## 📞 Support

**If Stuck:**
1. Read feature brief (`01_feature_brief.md`) again
2. Check verification steps in implementation files
3. Review common pitfalls sections
4. Log issue to debug workspace:
   ```
   C:\Users\ndemi\Desktop\Claude\handoffs\isaac\to_debug\
       command_framework_issue.md
   ```

---

## 🎯 Remember

- **Read feature brief first** - Understand the architecture
- **Execute in order** - Dependencies matter
- **Test at checkpoints** - Catch issues early
- **Document issues** - Fill out completion report thoroughly
- **One file at a time** - Don't rush, focus on quality

---

**Good luck! This is the foundation for Isaac's command execution. Take your time and build it right. 🚀**
