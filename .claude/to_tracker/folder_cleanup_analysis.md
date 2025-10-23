# Outdated Folders Identified for Cleanup

## Folders That Can Be Safely Removed

### `home/` and `work/` folders
**Status:** Outdated codebase copies - can be deleted
- Both use old single-file command structure (backup.py, help.py, etc.)
- `isaac/` folder uses modern manifest-based structure (command.yaml + run.py in subfolders)
- `isaac/` has 15+ commands vs 4 basic ones in home/work
- No active references to these folders in the codebase

### `old proman base files/` folder
**Status:** Moved to `reference/` folder for safekeeping
- Contains 8 legacy project management tools created pre-Isaac
- Moved to `reference/` folder with documentation
- Keep as reference for future feature integration

### `isaac/commands/restore.py` file
**Status:** Outdated - can be deleted
- Old handler-style implementation
- Replaced with manifest-based `isaac/commands/restore/` directory
- Contains complex legacy code that's been simplified in new implementation

## Current Active Structure
- `isaac/` - **ACTIVE** - Complete Isaac 2.0 implementation with manifest-based commands
- `reference/` - **ARCHIVE** - Legacy tools for reference/integration
- All other folders cleaned up

## Commands Available in Active Isaac:
- `/alias`, `/analyze`, `/ask`, `/backup`, `/config`, `/help`, `/list`, `/mine`, `/newfile`, `/queue`, `/restore`, `/save`, `/status`, `/summarize`, `/sync`
- Plus task mode and natural language commands