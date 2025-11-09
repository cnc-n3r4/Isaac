# Command Schema Standardization - Migration Guide

**Version:** 1.0
**Date:** 2025-11-09
**Task:** Phase 2.5 - Command Schema Standardization

## Table of Contents

1. [Overview](#overview)
2. [Why Standardization?](#why-standardization)
3. [Architecture](#architecture)
4. [Migration Steps](#migration-steps)
5. [Core Components](#core-components)
6. [Examples](#examples)
7. [Testing](#testing)
8. [Checklist](#checklist)

---

## Overview

This guide documents the command schema standardization effort (Task 2.5) which introduces a unified base class system for all Isaac commands. The goal is to ensure consistency, maintainability, and predictability across the codebase.

### What Changed?

- **Before**: Commands used ad-hoc argparse implementations with inconsistent patterns
- **After**: All commands inherit from `BaseCommand` with standardized interfaces

### Migration Status

✅ **Completed (5/10)**:
- `read` - File reading with line numbers
- `write` - File creation with overwrite support
- `edit` - String replacement in files
- `grep` - Pattern searching in files
- `glob` - File pattern matching

⏳ **Pending (5/10)**:
- `ask` - AI chat interface
- `analyze` - Code analysis
- `status` - System status
- `config` - Configuration management
- `help` - Help system

---

## Why Standardization?

### Problems Addressed

1. **Inconsistent Interfaces**: Commands had different argument parsing styles
2. **Code Duplication**: Same logic repeated across multiple commands
3. **Hard to Test**: Tight coupling made unit testing difficult
4. **Output Formats**: Multiple output formats without clear separation
5. **Maintenance**: Changes required updating many similar files

### Benefits

- ✅ **Consistency**: All commands follow the same pattern
- ✅ **Maintainability**: Changes to base class affect all commands
- ✅ **Testability**: Easy to mock and unit test
- ✅ **Documentation**: Auto-generated help from manifests
- ✅ **Type Safety**: Proper type hints throughout
- ✅ **Output Handling**: Unified response format

---

## Architecture

### Component Overview

```
isaac/commands/
├── base.py                    # Base classes (NEW)
│   ├── CommandManifest        # Command metadata
│   ├── CommandResponse        # Standard response format
│   ├── FlagParser             # Unified argument parsing
│   ├── BaseCommand            # Abstract base class
│   └── run_command()          # Universal entry point
│
├── TEMPLATE.py                # Template for new commands (NEW)
│
└── <command_name>/
    ├── command_impl.py        # Command implementation (NEW)
    ├── run.py                 # Entry point (UPDATED)
    └── command.yaml           # Metadata (EXISTING)
```

### Class Hierarchy

```
BaseCommand (ABC)
    ├── execute()              # Abstract - command logic
    ├── get_manifest()         # Abstract - metadata
    ├── get_help()             # Auto-generated help
    ├── run_standalone()       # Direct CLI execution
    ├── run_dispatcher()       # Through dispatcher
    └── run_piped()            # With piped input
```

---

## Core Components

### 1. CommandManifest

Defines command metadata:

```python
@dataclass
class CommandManifest:
    name: str              # Command name (e.g., "read")
    description: str       # One-line description
    usage: str            # Usage pattern
    examples: List[str]   # Example commands
    tier: int             # Safety tier (1-4)
    aliases: List[str]    # Alternative names
    category: str         # Command category
```

**Safety Tiers**:
- **Tier 1**: Safe read-only operations (read, grep, glob)
- **Tier 2**: File modifications (write, edit)
- **Tier 3**: Requires AI validation
- **Tier 4**: Dangerous operations (rm, chmod, etc.)

### 2. CommandResponse

Standard response format:

```python
class CommandResponse:
    success: bool                    # Success/failure
    data: Any                        # Result data
    error: str                       # Error message (if failed)
    metadata: Dict[str, Any]         # Additional info

    # Output format converters:
    to_dict()                        # Dict format
    to_envelope()                    # Dispatcher format
    to_blob()                        # Piping format
```

### 3. FlagParser

Unified argument parsing:

```python
parser = FlagParser(args)

# Positional arguments
file_path = parser.get_positional(0)
content = parser.get_positional(1)

# Flags with defaults
overwrite = parser.get_flag('overwrite', default=False)
output = parser.get_flag('output', default='files')

# Flags with aliases
ignore_case = parser.get_flag('ignore-case', aliases=['i'])
```

### 4. BaseCommand

Abstract base class for all commands:

```python
class MyCommand(BaseCommand):
    def execute(self, args: List[str], context: Optional[Dict[str, Any]]) -> CommandResponse:
        # Your implementation
        pass

    def get_manifest(self) -> CommandManifest:
        return CommandManifest(
            name="mycommand",
            description="What it does",
            usage="/mycommand <args>",
            examples=["example1", "example2"],
            tier=1,
            aliases=["mc"],
            category="general"
        )
```

---

## Migration Steps

### Step 1: Create `command_impl.py`

Create `isaac/commands/<command>/command_impl.py`:

```python
"""
<Command> - Standardized Implementation
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.tools import <YourTool>


class <YourCommand>(BaseCommand):
    """Brief description"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        parser = FlagParser(args)

        # Parse arguments
        arg1 = parser.get_positional(0)
        flag1 = parser.get_flag('flag-name', default=False)

        # Validate
        if not arg1:
            return CommandResponse(
                success=False,
                error="Argument required",
                metadata={"error_code": "MISSING_ARGUMENT"}
            )

        # Execute
        try:
            # Your logic here
            result = do_something(arg1, flag1)

            return CommandResponse(
                success=True,
                data=result,
                metadata={"arg1": arg1}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                error=str(e),
                metadata={"error_code": "EXECUTION_ERROR"}
            )

    def get_manifest(self) -> CommandManifest:
        return CommandManifest(
            name="yourcommand",
            description="One-line description",
            usage="/yourcommand <arg1> [--flag]",
            examples=[
                "/yourcommand example1",
                "/yourcommand example2 --flag"
            ],
            tier=2,
            aliases=["yc"],
            category="file"
        )
```

### Step 2: Update `run.py`

Simplify `isaac/commands/<command>/run.py`:

```python
"""
<Command> - Entry Point
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import run_command
from isaac.commands.<command>.command_impl import <YourCommand>


def main():
    """Main entry point for /<command>"""
    command = <YourCommand>()
    run_command(command)


if __name__ == "__main__":
    main()
```

### Step 3: Test All Modes

Test your command in all execution modes:

#### A. Standalone Mode
```bash
python isaac/commands/yourcommand/run.py arg1 --flag
```

#### B. Dispatcher Mode
```bash
echo '{"command": "/yourcommand arg1", "manifest": {}}' | python isaac/commands/yourcommand/run.py
```

#### C. Piped Mode
```bash
echo '{"kind": "text", "content": "data", "meta": {"command": "/yourcommand"}}' | python isaac/commands/yourcommand/run.py
```

### Step 4: Backup Original

Before replacing, backup the original:

```bash
cp isaac/commands/yourcommand/run.py isaac/commands/yourcommand/run.py.backup
```

### Step 5: Update and Test

1. Replace the `run.py` with standardized version
2. Run comprehensive tests
3. Verify all modes work correctly
4. Update command.yaml if needed

---

## Examples

### Example 1: Simple File Operation (Read)

**Before** (87 lines):
```python
import argparse
import json
import sys

def main():
    parser = argparse.ArgumentParser(...)
    # 70+ lines of argparse setup, execution, output formatting
```

**After** (95 lines with command_impl, 25 lines for run.py):
```python
# command_impl.py (70 lines)
class ReadCommand(BaseCommand):
    def execute(self, args, context):
        parser = FlagParser(args)
        file_path = parser.get_positional(0)
        # Clean implementation

# run.py (18 lines)
def main():
    command = ReadCommand()
    run_command(command)
```

### Example 2: Complex Search (Grep)

**Before** (128 lines):
- Mixed argparse and output logic
- Hard-coded envelope format
- Difficult to test

**After** (150 lines split):
- `command_impl.py`: 130 lines focused logic
- `run.py`: 18 lines simple entry point
- Easy to test, mock, and extend

### Example 3: With Piped Input (Write)

```python
def execute(self, args, context):
    parser = FlagParser(args)
    file_path = parser.get_positional(0)
    content = parser.get_positional(1)

    # Check for piped content
    if content is None and context and "piped_input" in context:
        content = context["piped_input"]

    # Validate and execute
    if not content:
        return CommandResponse(
            success=False,
            error="Content required"
        )
```

---

## Testing

### Unit Testing Commands

```python
import pytest
from isaac.commands.read.command_impl import ReadCommand

def test_read_command_success():
    command = ReadCommand()
    result = command.execute(['test.txt'], context=None)

    assert result.success == True
    assert result.data is not None

def test_read_command_missing_arg():
    command = ReadCommand()
    result = command.execute([], context=None)

    assert result.success == False
    assert "required" in result.error.lower()

def test_read_command_with_offset():
    command = ReadCommand()
    result = command.execute(['test.txt', '--offset', '10'], context=None)

    assert result.success == True
    assert result.metadata['offset'] == 10
```

### Integration Testing

```python
def test_read_command_standalone():
    """Test direct execution"""
    result = subprocess.run(
        ['python', 'isaac/commands/read/run.py', 'test.txt'],
        capture_output=True
    )
    assert result.returncode == 0

def test_read_command_piped():
    """Test with piped input"""
    blob = json.dumps({
        "kind": "text",
        "content": "piped data",
        "meta": {"command": "/read test.txt"}
    })
    result = subprocess.run(
        ['python', 'isaac/commands/read/run.py'],
        input=blob,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
```

### Test Checklist

- [ ] Standalone mode works
- [ ] Dispatcher mode works
- [ ] Piped mode works (if applicable)
- [ ] All flags parsed correctly
- [ ] Error handling works
- [ ] Help text displays correctly
- [ ] Metadata is accurate
- [ ] Unit tests pass
- [ ] Integration tests pass

---

## Checklist

### Pre-Migration
- [ ] Read this guide completely
- [ ] Understand BaseCommand pattern
- [ ] Review TEMPLATE.py
- [ ] Backup existing command

### During Migration
- [ ] Create command_impl.py
- [ ] Implement execute() method
- [ ] Implement get_manifest() method
- [ ] Handle piped input (if needed)
- [ ] Add proper error handling
- [ ] Update run.py to use run_command()

### Post-Migration
- [ ] Test standalone mode
- [ ] Test dispatcher mode
- [ ] Test piped mode
- [ ] Write unit tests
- [ ] Update documentation
- [ ] Remove backup file (after verification)

### Code Quality
- [ ] Type hints added
- [ ] Docstrings complete
- [ ] Error codes consistent
- [ ] Examples helpful
- [ ] No code duplication
- [ ] PEP 8 compliant

---

## Common Patterns

### Pattern 1: File Operations

```python
def execute(self, args, context):
    parser = FlagParser(args)
    file_path = parser.get_positional(0)

    if not file_path:
        return CommandResponse(
            success=False,
            error="File path required",
            metadata={"error_code": "MISSING_ARGUMENT"}
        )

    try:
        tool = ReadTool()
        result = tool.execute(file_path=file_path)

        return CommandResponse(
            success=True,
            data=result["content"],
            metadata={"file_path": file_path}
        )
    except Exception as e:
        return CommandResponse(
            success=False,
            error=str(e),
            metadata={"error_code": "EXECUTION_ERROR"}
        )
```

### Pattern 2: AI Integration

```python
def execute(self, args, context):
    parser = FlagParser(args)
    query = " ".join(parser.get_all_positional())

    # Check for piped input
    if context and "piped_input" in context:
        query += f"\n\nContext:\n{context['piped_input']}"

    # Get AI client
    config = context.get("config", {})
    client = get_ai_client(config)

    # Query AI
    response = client.chat(query)

    return CommandResponse(
        success=True,
        data=response,
        metadata={"query": query}
    )
```

### Pattern 3: Multi-Output Modes

```python
def execute(self, args, context):
    parser = FlagParser(args)
    output_mode = parser.get_flag('output', default='text')

    # Execute command
    result = do_something()

    # Format based on mode
    if output_mode == 'json':
        data = json.dumps(result, indent=2)
    elif output_mode == 'table':
        data = format_table(result)
    else:
        data = format_text(result)

    return CommandResponse(
        success=True,
        data=data,
        metadata={"output_mode": output_mode}
    )
```

---

## Troubleshooting

### Issue: Import errors

**Solution**: Check path insertion in both files:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
```

### Issue: FlagParser not working

**Solution**: Ensure you're passing the correct argument list:
```python
# Wrong:
parser = FlagParser(sys.argv)  # Includes script name

# Right:
parser = FlagParser(args)  # Already stripped command name
```

### Issue: Output format not working

**Solution**: Use the correct converter:
- Standalone: `data` field is printed
- Dispatcher: Use `to_envelope()`
- Piped: Use `to_blob(command)`

### Issue: Tests failing

**Solution**: Check execution mode detection:
```python
# In tests, mock stdin:
with patch('sys.stdin.isatty', return_value=True):
    command.run_standalone(args)
```

---

## References

- **Phase 2 Kickoff**: `/home/user/Isaac/PHASE_2_KICKOFF.md`
- **Template**: `/home/user/Isaac/isaac/commands/TEMPLATE.py`
- **Base Classes**: `/home/user/Isaac/isaac/commands/base.py`

## Migrated Commands

### Read Command
- **File**: `isaac/commands/read/command_impl.py`
- **Status**: ✅ Complete
- **Tier**: 1 (Safe)
- **Notes**: Handles offset/limit for partial file reading

### Write Command
- **File**: `isaac/commands/write/command_impl.py`
- **Status**: ✅ Complete
- **Tier**: 2 (Needs validation)
- **Notes**: Supports piped input and overwrite flag

### Edit Command
- **File**: `isaac/commands/edit/command_impl.py`
- **Status**: ✅ Complete
- **Tier**: 2 (Needs validation)
- **Notes**: Exact string replacement with replace-all option

### Grep Command
- **File**: `isaac/commands/grep/command_impl.py`
- **Status**: ✅ Complete
- **Tier**: 1 (Safe)
- **Notes**: Multiple output modes (files, content, count)

### Glob Command
- **File**: `isaac/commands/glob/command_impl.py`
- **Status**: ✅ Complete
- **Tier**: 1 (Safe)
- **Notes**: Pattern-based file finding

---

## Next Steps

1. **Continue Migration**: Migrate remaining 5 commands (ask, analyze, status, config, help)
2. **Command Registry**: Create central registry for all standardized commands
3. **Auto-Discovery**: Implement automatic command discovery from manifests
4. **Documentation**: Auto-generate command reference from manifests
5. **Validation**: Add schema validation for command manifests

---

**Status**: 5 of 10 commands migrated (50%)
**Target**: 30 of 42 total commands standardized (71%)
**Progress**: On track for Task 2.5 completion

Last Updated: 2025-11-09
