# UI Simplification Cleanup - Obsolete Test Files

## Files to Delete
The following test files test the old TerminalControl-based UI that was replaced by the simplified PermanentShell interface. These tests are obsolete and should be deleted:

### Obsolete Test Files (Delete These)
- `tests/test_clear.py` - Tests clear command preserving status bar (obsolete UI paradigm)
- `tests/test_cursor_positioning.py` - Tests complex cursor positioning (obsolete)
- `tests/test_natural_stacking.py` - Tests command stacking with status bars (obsolete)
- `tests/test_quick.py` - Tests quick operations with old UI (obsolete)
- `tests/test_scroll_region.py` - Tests scroll regions (obsolete UI feature)
- `tests/test_status.py` - Tests status bar updates (obsolete)
- `tests/test_terminal_scrolling.py` - Tests terminal scrolling (obsolete)
- `tests/test_ui_components.py` - Tests old UI components (obsolete)

### Partially Obsolete (Review/Modify)
- `tests/test_special_commands.py` - Tests both TerminalControl AND PermanentShell. The PermanentShell parts may be relevant, but TerminalControl dependencies should be removed.

## Files to Keep
- Any tests that specifically test `PermanentShell` functionality
- Integration tests that work with the new simplified UI
- Tests that don't depend on the old TerminalControl interface

## Action Required
Delete the obsolete test files listed above. They test UI functionality that no longer exists in the ui-simplification branch.

## Verification
After cleanup, run `pytest tests/` to ensure remaining tests pass and no imports fail.