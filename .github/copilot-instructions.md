# Isaac 2.0 MVP - AI Agent Instructions

## Architecture Overview
Isaac is a multi-platform shell assistant that wraps PowerShell/bash with a 5-tier command safety system and cloud-synced sessions. It provides a permanent shell layer with AI-powered command validation and natural language support.

**Core Components:**
- `isaac/core/`: Tier validation, command routing, session management
- `isaac/adapters/`: Shell abstraction (PowerShellAdapter, BashAdapter, ShellDetector)
- `isaac/models/`: Preferences, CommandHistory for data persistence
- `isaac/ui/`: Splash screen, header display, terminal control
- `isaac/api/`: Cloud sync client for PHP API integration
- `php_api/`: GoDaddy-hosted backend for session roaming

**Data Flow:** User input → TierValidator.get_tier() → ShellAdapter.execute() → Cloud sync

## Developer Workflows

### Build & Setup
```bash
pip install -e .  # Install in development mode
pytest tests/ --cov=isaac --cov-report=term-missing  # Run tests with coverage
```

### Testing
- Use pytest exclusively; aim for ≥85% coverage
- Tests in `tests/` validate tier classification (safety-critical)
- Run `pytest tests/test_tier_validator.py -v` for core validation

### Deployment
- Python package via `setup.py`
- PHP API deploys to GoDaddy shared hosting
- User launches with `isaac --start` for permanent shell session

## Project Conventions

### Tier System Pattern
Commands classified 1-4 (1=instant, 4=lockdown):
```python
# From isaac/core/tier_validator.py
tier = validator.get_tier(command)
if tier == 1:
    execute_immediately()
elif tier == 4:
    require_exact_confirmation()
```

### Shell Abstraction
All shell operations through adapters:
```python
# Base interface in isaac/adapters/base_adapter.py
class BaseShellAdapter:
    def execute(self, command: str) -> CommandResult: ...
```

### Configuration Loading
Use Path-based config from `isaac/data/`:
```python
data_dir = Path(__file__).parent.parent / 'data'
config = json.load((data_dir / 'tier_defaults.json').open())
```

### Error Handling
Return structured results, not exceptions:
```python
@dataclass
class CommandResult:
    success: bool
    output: str
    exit_code: int
```

## Key Files
- `isaac_mvp/00_run_order.yaml`: Build sequence and dependencies
- `isaac/data/tier_defaults.json`: Command safety mappings
- `tests/test_tier_validator.py`: Safety validation tests
- `php_api/`: Cloud sync endpoints

## Integration Points
- PHP API: Session sync via HTTP POST/GET
- Shell detection: Auto-detect PowerShell vs bash on startup
- Cross-platform paths: Use `Path` for OS-agnostic file handling</content>
<parameter name="filePath">c:\Projects\Isaac\.github\copilot-instructions.md