# Isaac 2.0 - Multi-Platform Shell Assistant

Intelligent shell wrapper with cloud-synced sessions and 5-tier command validation.

## Features
- Multi-platform (PowerShell + bash)
- Cloud session roaming across machines
- 5-tier command safety system
- Splash screen + locked header UI
- Natural language queries (Phase 2)

## Installation

```bash
pip install -e .
```

## Usage

```bash
isaac --start
```

## Commands

Isaac supports three types of commands:

### Regular Commands (no prefix)
Execute shell commands normally:
```bash
ls
dir
cd /path/to/dir
```

### Local Meta-Commands (/)
Built-in Isaac commands:
```bash
/help     - Show available commands
/version  - Show Isaac version
/status   - Show system status
/config   - Show current configuration
/ask      - Ask AI questions (e.g., /ask what is the capital of France?)
```

### AI Integration
```bash
# x.ai collection management
/togrok create my_collection
/togrok upload my_collection file.txt
/togrok search my_collection "query"
/togrok list
```

### Distributed Commands (!)
Remote command execution (coming soon):
```bash
!machine_name command
!list  # List available machines
```

## Requirements
- Python 3.8+
- Windows (PowerShell 7+ or 5.1) OR Linux (bash)
- GoDaddy hosting (for cloud sync)

## Project Structure
```
isaac/
├── core/          # Session management, command routing, tier validation
├── adapters/      # Shell abstraction (PowerShell, bash)
├── api/           # Cloud sync client
├── ui/            # Terminal control, splash, header, prompt
├── models/        # Data structures (preferences, command history)
├── utils/         # Config loader, logging, validators
└── data/          # Static data (tier defaults, splash art)
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Launch Isaac
isaac --start
```

## License
MIT