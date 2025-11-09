# Isaac Directory Cleanup Plan

## Files/Folders to REMOVE (Dead/Redundant)

### Duplicate/Old Code Folders
- `home/` - Old duplicate of isaac code (372KB)
- `work/` - Another old duplicate (176KB)
- `.archive/` - Archived files
- `__pycache__/` - Python cache at root level
- `isaac.egg-info/` - Build artifact

### Old Documentation/Specs
- `docs/` - Old documentation folder
- `instructions/` - Old specification documents
- `CHERRY_PICK_STATUS.md` - Obsolete tracking
- `CLAUDE_CODE_TRANSFORMATION_PLAN.md` - Old plan
- `MERGE_PLAN.md` - Obsolete merge tracking
- `TEST_RESULTS.md` - Old test results
- `TOOLS_TEST_REPORT.md` - Old test report
- `TRACK1.2_START.md` - Old tracking
- `test_fixes.md` - Old notes
- `XAI_SDK_INTEGRATION_SUMMARY.md` - Old summary
- `XAI_SDK_SEARCH_FIX.md` - Old fix notes

### Debug/Test Files
- `check_config.py` - Debug script
- `debug_config_loading.py` - Debug script
- `debug_config.py` - Debug script
- `debug_terminal_control.py` - Empty debug file
- `show_raw_config.py` - Debug script
- `simple_test.py` - Empty test file
- `test_ai_persistence.py` - Old test
- `test_bar_header.py` - Empty test
- `test_config_console.py` - Old test
- `test_header.py` - Empty test
- `test_prefix_system.py` - Old test
- `test_xai_sdk.py` - Old test
- `test_collections_integration.py` - Old test
- `.coverage` - Coverage data

### Random Text Files
- `gangstar.txt` - Random text
- `maddona.txt` - Random text
- `pipeline_test.txt` - Test output
- `saved_output.txt` - Test output
- `test_output.txt` - Test output
- `test_pipe.txt` - Test output
- `example_prompt.md` - Old example

### Unused Components
- `php_api/` - PHP files not needed for Python project
- `Isaac-1.code-workspace` - Duplicate workspace file
- `.claude/` - Can be regenerated if needed

## Files to KEEP (Active/Needed)

### Core Code
- `isaac/` - Main codebase (1.3MB)
- `tests/` - Unit tests
- `venv/` - Virtual environment

### Configuration
- `setup.py`
- `requirements.txt`
- `.gitignore`

### Documentation (Current)
- `README.md`
- `LICENSE`
- `AI_ROUTING_BUILD_SUMMARY.md`
- `QUICK_START_AI.md`
- `ISAAC_COMMAND_REFERENCE.md`

### Testing
- `test_ai_router.py` - New AI tests
- `demo_agent.py` - New demo

### Git
- `.git/`
- `.github/`

### Workspace
- `Isaac.code-workspace` - Keep one
