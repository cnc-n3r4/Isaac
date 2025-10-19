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