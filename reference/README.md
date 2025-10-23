# Reference Codebase - Legacy Project Management Suite

This folder contains the original "proman" (project management) suite that served as the foundation for many Isaac features. These files were created as standalone tools before being integrated into the Isaac shell assistant.

## Files Overview

### Core Project Management Tools
- **`aliaspro.py`** - Project-scoped command aliases with variable expansion
- **`newfile.py`** - Template-based file creation with project context
- **`setpro.py`** - Project settings and configuration management
- **`proske.py`** - Project skeleton/initialization tool

### Development Workflow Tools
- **`depman.py`** - Dependency management and requirements handling
- **`packpro.py`** - Project packaging and distribution
- **`gopro.py`** - Project navigation and workspace management

### CNC-Specific Tools
- **`cpf.py`** - CNC program file management and validation

## Integration Status

These tools are referenced in the refactor backlog (`.claude/mail/to_refactor/proman_suite_integration.md`) for potential integration into Isaac as native commands. Features like:

- Template-based file creation (newfile) → `/newfile` command
- Project aliases (aliaspro) → potential `/alias` command
- CNC file handling (cpf) → integration with collections feature

## Usage Notes

These are standalone Python scripts that can be run independently:
```bash
python aliaspro.py --help
python newfile.py --help
# etc.
```

They use JSON configuration files and support project-specific settings through `.proman.json` files.

## Historical Context

Created as a suite of command-line tools for CNC programming and project management before evolving into the AI-enhanced shell assistant that Isaac became.