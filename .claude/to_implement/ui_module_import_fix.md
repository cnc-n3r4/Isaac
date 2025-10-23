# UI Module Import Issues - Implementation Handoff

## Problem
Multiple tests are failing with `ModuleNotFoundError: No module named 'isaac.ui.terminal_control'`. The tests expect a `terminal_control.py` module that doesn't exist.

## Current UI Structure
```
isaac/ui/
├── config_console.py
├── header_display.py
├── permanent_shell.py
├── prompt_handler.py
├── splash_screen.py
├── visual_enhancer.py
└── _archived/
```

## Affected Tests
- test_clear.py
- test_cursor_positioning.py
- test_natural_stacking.py
- test_quick.py
- test_scroll_region.py
- test_special_commands.py
- test_status.py
- test_terminal_scrolling.py
- test_ui_components.py

## Required Actions

### 1. Create Missing Module
Create `isaac/ui/terminal_control.py` that provides the expected interface, or update the existing modules to provide the required functionality.

### 2. Update Imports
Update test files to import from the correct modules, or ensure backward compatibility.

### 3. Verify Functionality
Ensure all UI functionality still works after the ui-simplification changes.

## Implementation Notes
- Check what functionality `TerminalControl` class should provide
- Look at existing UI modules to see if functionality was moved
- Consider if tests need updating vs. creating the missing module

## Priority: High
This is blocking test execution and needs to be resolved before further development.</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_implement\ui_module_import_fix.md