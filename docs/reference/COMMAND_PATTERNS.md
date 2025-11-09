# COMMAND IMPLEMENTATION PATTERNS
**Project:** ISAAC Command System Analysis
**Agent:** Agent 2 - Command System Auditor
**Date:** 2025-11-09

---

## EXECUTIVE SUMMARY

ISAAC commands use **7 distinct implementation patterns**, ranging from clean, standardized approaches to complex, ad-hoc solutions. This document analyzes each pattern, identifies best practices to promote and anti-patterns to eliminate.

**Key Findings:**
- **Pattern A** (argparse + Tool Wrapper) is the **gold standard** ✅
- **Pattern B** (stdin-json + JSON Envelope) is acceptable for dispatcher-only commands ✅
- **Pattern F** (Custom sys.argv parsing) should be **eliminated** ❌
- **Pattern G** (Placeholders/Stubs) should be **removed** ❌

---

## TABLE OF CONTENTS

1. [Pattern Taxonomy](#1-pattern-taxonomy)
2. [Pattern A: argparse + Tool Wrapper](#2-pattern-a-argparse--tool-wrapper) ✅ **GOLD STANDARD**
3. [Pattern B: stdin-json + JSON Envelope](#3-pattern-b-stdin-json--json-envelope) ✅ Recommended
4. [Pattern C: stdin-json + Custom Flag Parser](#4-pattern-c-stdin-json--custom-flag-parser) ⚠️ Refactor
5. [Pattern D: Command Class Delegate](#5-pattern-d-command-class-delegate) ⚠️ Improve
6. [Pattern E: Hybrid stdin-json/sys.argv](#6-pattern-e-hybrid-stdin-jsonsysargv) ❌ Eliminate
7. [Pattern F: Manual sys.argv Parsing](#7-pattern-f-manual-sysargv-parsing) ❌ Eliminate
8. [Pattern G: Placeholder/Stub](#8-pattern-g-placeholderstub) ❌ Remove
9. [Best Practices Matrix](#9-best-practices-matrix)
10. [Anti-Patterns to Eliminate](#10-anti-patterns-to-eliminate)
11. [Migration Guidelines](#11-migration-guidelines)

---

## 1. PATTERN TAXONOMY

### 1.1 Overview Table

| Pattern | Count | Quality | Maintenance | Recommendation |
|---------|-------|---------|-------------|----------------|
| **A: argparse + Tool** | 10 | ⭐⭐⭐⭐⭐ | Easy | ✅ **Use for all new commands** |
| **B: stdin-json + envelope** | 12 | ⭐⭐⭐⭐ | Easy | ✅ Use for dispatcher-only |
| **C: stdin-json + custom parser** | 2 | ⭐⭐⭐ | Medium | ⚠️ Refactor to A or B |
| **D: Command class delegate** | 3 | ⭐⭐⭐ | Medium | ⚠️ Add envelope output |
| **E: Hybrid stdin/sys.argv** | 3 | ⭐⭐ | Hard | ❌ Migrate to A |
| **F: Manual sys.argv** | 8 | ⭐⭐ | Hard | ❌ Migrate to A |
| **G: Placeholder/Stub** | 4 | ⭐ | N/A | ❌ Delete or complete |

### 1.2 Pattern Distribution

```
Pattern A (argparse + Tool):     20% ████████████
Pattern B (stdin-json):          24% ██████████████
Pattern C (custom parser):        4% ██
Pattern D (class delegate):       6% ███
Pattern E (hybrid):               6% ███
Pattern F (manual sys.argv):     16% █████████
Pattern G (placeholder):          8% ████
Unknown/Not analyzed:            16% █████████
```

---

## 2. PATTERN A: argparse + Tool Wrapper

### 2.1 Description

**Gold standard pattern** for standalone commands that can be called interactively or through dispatcher.

**Characteristics:**
- Uses `argparse.ArgumentParser` for argument parsing
- Wraps a tool class from `isaac.tools` (ReadTool, WriteTool, etc.)
- Dual output: Human-readable for TTY, JSON envelope for non-TTY
- Comprehensive help text with examples
- Proper error handling with try-except

**Commands Using This Pattern:**
1. `/edit` - Edit files (EditTool)
2. `/file` - Unified file operations (multiple tools)
3. `/glob` - Find files (GlobTool)
4. `/grep` - Search files (GrepTool)
5. `/read` - Read files (ReadTool)
6. `/write` - Write files (WriteTool)
7. `/search` - Unified search (GlobTool + GrepTool)
8. `/newfile` - Create files with templates

### 2.2 Example Implementation

**File**: `isaac/commands/read/run.py`

```python
#!/usr/bin/env python3
"""
Read Command - Read files with line numbers
Wrapper for ReadTool
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from isaac.tools import ReadTool


def main():
    """Main entry point for /read command"""
    parser = argparse.ArgumentParser(description='Read files with line numbers')
    parser.add_argument('file_path', help='Path to file to read')
    parser.add_argument('--offset', type=int, default=0,
                       help='Line number to start from (0-indexed)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Maximum number of lines to read')
    parser.add_argument('--help-cmd', action='store_true', help='Show this help')

    try:
        # Show help if no arguments
        if len(sys.argv) == 1:
            parser.print_help()
            print("\nExamples:")
            print("  /read myfile.py")
            print("  /read myfile.py --offset 100")
            print("  /read myfile.py --limit 50")
            sys.exit(0)

        args = parser.parse_args()

        if args.help_cmd:
            parser.print_help()
            sys.exit(0)

        # Execute tool
        tool = ReadTool()
        result = tool.execute(
            file_path=args.file_path,
            offset=args.offset,
            limit=args.limit
        )

        # Output result
        if result['success']:
            print(result['content'])

            # Print summary to stderr (doesn't interfere with piping)
            if args.limit or args.offset:
                summary = f"\n[Read {result['lines_read']} of {result['total_lines']} lines]"
                print(summary, file=sys.stderr)

            # Return success envelope for dispatcher
            if not sys.stdout.isatty():
                envelope = {
                    "ok": True,
                    "stdout": result['content']
                }
                print(json.dumps(envelope))
        else:
            print(f"Error: {result['error']}", file=sys.stderr)

            if not sys.stdout.isatty():
                envelope = {
                    "ok": False,
                    "error": {"message": result['error']}
                }
                print(json.dumps(envelope))

            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

        if not sys.stdout.isatty():
            envelope = {
                "ok": False,
                "error": {"message": str(e)}
            }
            print(json.dumps(envelope))

        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 2.3 Strengths

✅ **Clear separation of concerns** - Parsing separate from logic
✅ **Standard Python library** - argparse is well-known
✅ **Excellent help text** - Built-in `--help` support
✅ **Dual-mode output** - Works in both interactive and programmatic contexts
✅ **Error handling** - Consistent JSON envelope for errors
✅ **Testable** - Easy to unit test argument parsing
✅ **Maintainable** - New developers can understand quickly

### 2.4 Weaknesses

⚠️ **Verbose** - More lines of code than simpler patterns
⚠️ **Dual output logic** - TTY detection adds complexity
⚠️ **Tool dependency** - Requires separate Tool class implementation

### 2.5 When to Use

**Use Pattern A when:**
- Command can be called both interactively and via dispatcher
- Command has multiple arguments or flags
- Command needs comprehensive help text
- Command is user-facing (not just internal)

**Don't use Pattern A when:**
- Command is dispatcher-only (use Pattern B)
- Command is extremely simple (single argument, no flags)

### 2.6 Variants

**Variant A1: With Tool Wrapper** (Recommended)
- Most commands: read, write, edit, grep, glob
- Tool classes in `isaac/tools/`
- Command file is thin wrapper

**Variant A2: Direct Implementation** (Acceptable)
- Complex logic inline: `/file`, `/search`
- Still uses argparse, JSON envelope
- No separate tool class

---

## 3. PATTERN B: stdin-json + JSON Envelope

### 3.1 Description

**Standard pattern for dispatcher-only commands** that receive structured input via stdin.

**Characteristics:**
- Reads JSON payload from stdin: `json.loads(sys.stdin.read())`
- Payload structure: `{"args": {}, "session": {}, "manifest": {}}`
- Outputs JSON envelope: `{"ok": true/false, "stdout": "...", "meta": {}}`
- No interactive mode (dispatcher-only)

**Commands Using This Pattern:**
1. `/help` - Help system
2. `/status` - System status
3. `/machines` - Machine orchestration
4. `/config` - Configuration (extensive flags)
5. `/backup` - Backup (placeholder)
6. `/list` - List management (placeholder)

### 3.2 Example Implementation

**File**: `isaac/commands/status/run.py`

```python
#!/usr/bin/env python3
"""
Status Command Handler - Enhanced with AI session and workspace info
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def main():
    """Main entry point for status command"""
    # Read payload from stdin
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})
    session = payload.get("session", {})

    verbose = args.get("verbose", False)

    if verbose:
        output = get_detailed_status(session)
    else:
        output = get_summary_status(session)

    # Return envelope
    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {}
    }))


def get_summary_status(session):
    """Return one-line status summary"""
    machine_id = session.get('machine_id', 'unknown')[:6]
    # ... status logic ...
    return f"Session: {machine_id} | Workspace: {ws_status} | AI: {ai}"


def get_detailed_status(session):
    """Return detailed system status with AI session info"""
    lines = []
    lines.append("=" * 60)
    lines.append("ISAAC System Status")
    # ... detailed status logic ...
    return "\n".join(lines)


if __name__ == "__main__":
    main()
```

### 3.3 Strengths

✅ **Simple and clean** - Less boilerplate than argparse
✅ **Dispatcher-optimized** - Perfect for internal commands
✅ **Structured input** - JSON payload is self-documenting
✅ **Session access** - Easy access to session context
✅ **Consistent output** - Always JSON envelope

### 3.4 Weaknesses

⚠️ **No interactive mode** - Can't be run standalone easily
⚠️ **Manual arg parsing** - Must extract values from args dict
⚠️ **No built-in help** - Must implement help separately
⚠️ **Testing complexity** - Must mock stdin JSON

### 3.5 When to Use

**Use Pattern B when:**
- Command is dispatcher-only (not interactive)
- Command needs session context
- Command has simple arguments (1-3 flags)
- Command is internal/system (not user-facing)

**Don't use Pattern B when:**
- Command needs to be run standalone
- Command has complex arguments (5+ flags)
- Command needs comprehensive help text

---

## 4. PATTERN C: stdin-json + Custom Flag Parser

### 4.1 Description

**Hybrid pattern** combining stdin-json with custom flag parsing logic.

**Characteristics:**
- Reads stdin-json payload
- Implements custom `parse_flags()` function
- More flexible than args dict but less standard than argparse

**Commands Using This Pattern:**
1. `/alias` - Unix alias management (simple custom parser)
2. `/mine` - xAI Collections (complex custom parser, 1600 lines)

### 4.2 Example Implementation

**File**: `isaac/commands/alias/run.py` (excerpt)

```python
def parse_flags(args_list):
    """Parse command line flags using standardized syntax."""
    flags = {}
    positional = []
    i = 0

    while i < len(args_list):
        arg = args_list[i]

        if arg.startswith('--'):
            flag = arg[2:]  # Remove --
            # Check if next arg is the value
            if i + 1 < len(args_list) and not args_list[i + 1].startswith('-'):
                flags[flag] = args_list[i + 1]
                i += 1  # Skip the value
            else:
                flags[flag] = True  # Boolean flag
        else:
            positional.append(arg)

        i += 1

    return flags, positional


def main():
    """Main entry point for alias command"""
    try:
        # Read payload from stdin
        payload = json.loads(sys.stdin.read())
        args_raw = payload.get("args", [])
        session = payload.get("session", {})

        # Parse flags from args
        flags, positional = parse_flags(args_raw)

        # Determine action from flags
        if 'list' in flags:
            result = handle_list(translator)
        elif 'show' in flags:
            command = flags.get('show')
            result = handle_show(translator, command)
        # ... more handlers ...
```

### 4.3 Strengths

✅ **Flexible** - Can handle edge cases argparse doesn't
✅ **stdin-json compatible** - Works with dispatcher payload
✅ **Custom logic** - Can implement domain-specific parsing

### 4.4 Weaknesses

⚠️ **Maintenance burden** - Custom code to maintain
⚠️ **No validation** - Must implement type checking manually
⚠️ **No help generation** - argparse generates help automatically
⚠️ **Bug prone** - Edge cases in custom parsers

### 4.5 When to Use

**Use Pattern C when:**
- ❌ **DON'T USE** - Migrate to Pattern A or B instead

**Recommendation**: Refactor `/alias` to use argparse, keep `/mine` as-is (complex but well-designed).

---

## 5. PATTERN D: Command Class Delegate

### 4.1 Description

**Delegation pattern** where `run.py` delegates to a command class.

**Characteristics:**
- Thin `run.py` wrapper
- Main logic in `*_command.py` class
- Uses sys.argv for arguments

**Commands Using This Pattern:**
1. `/ambient` → `AmbientCommand`
2. `/learn` → `LearnCommand`
3. `/pair` → `PairCommand`

### 4.2 Example Implementation

**File**: `isaac/commands/learn/run.py`

```python
#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.commands.learn.learn_command import LearnCommand


def main():
    """Main entry point for /learn command"""
    try:
        command = LearnCommand()
        command.execute(sys.argv[1:])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup if needed
        pass


if __name__ == "__main__":
    main()
```

### 4.3 Strengths

✅ **Separation** - Command logic separate from entry point
✅ **Class organization** - OOP structure for complex commands
✅ **Reusability** - Command class can be imported elsewhere

### 4.4 Weaknesses

⚠️ **No JSON envelope** - Plain text output only
⚠️ **sys.argv** - Not dispatcher-optimized
⚠️ **Inconsistent** - Different from other patterns

### 4.5 When to Use

**Use Pattern D when:**
- Command is extremely complex (500+ lines)
- Command has multiple sub-operations
- Command needs to be imported as class

**Improvement Needed:**
- Add JSON envelope output support
- Consider stdin-json input option
- Add comprehensive help text

---

## 6. PATTERN E: Hybrid stdin-json/sys.argv

### 4.1 Description

**Anti-pattern** that tries to support both stdin-json and sys.argv input.

**Characteristics:**
- Complex input detection logic
- Different behavior based on invocation method
- Multiple output formats

**Commands Using This Pattern:**
1. `/ask` - AI chat (blob/envelope/plain text modes)
2. `/msg` - Message queue
3. `/tasks` - Task management

### 4.2 Example (Anti-Pattern)

**File**: `isaac/commands/ask/run.py` (excerpt)

```python
def main():
    """Main entry point for ask command"""
    return_blob = False
    try:
        # Check if we're being called through dispatcher or standalone
        if not sys.stdin.isatty():
            stdin_data = sys.stdin.read()

            # Try to parse as blob format first
            try:
                blob = json.loads(stdin_data)
                if isinstance(blob, dict) and 'kind' in blob:
                    # This is piped input in blob format
                    return_blob = True
                elif isinstance(blob, dict) and 'manifest' in blob:
                    # This is dispatcher payload
                    return_blob = False
                else:
                    # Unknown JSON format
                    return_blob = True
            except json.JSONDecodeError:
                # Not JSON, treat as plain text input
                return_blob = True
        else:
            # Standalone execution - get query from command line args
            query = ' '.join(sys.argv[1:])
            return_blob = False

        # ... 200 more lines of mode-specific logic ...
```

### 4.3 Strengths

❓ **Flexibility?** - Supports multiple invocation methods
❓ **Backward compatibility?** - Maintains old behavior

### 4.4 Weaknesses

❌ **Extremely complex** - 350 lines with nested conditionals
❌ **Hard to maintain** - Mode detection is fragile
❌ **Inconsistent behavior** - Same command, different outputs
❌ **Testing nightmare** - Must test all modes
❌ **Bug prone** - Edge cases abound

### 4.5 When to Use

**Use Pattern E when:**
- ❌ **NEVER** - This is an anti-pattern

**Recommendation**:
- Migrate `/ask` to single mode (envelope only)
- Migrate `/msg` and `/tasks` to stdin-json only
- Create separate standalone wrappers if needed

---

## 7. PATTERN F: Manual sys.argv Parsing

### 4.1 Description

**Anti-pattern** with manual parsing of `sys.argv` without argparse.

**Characteristics:**
- Accesses `sys.argv[1]`, `sys.argv[2]` directly
- Manual flag detection (`if arg.startswith('--')`)
- No structured parsing

**Commands Using This Pattern:**
1. `/machine` - Machine registry (most complex)
2. `/images` - Cloud image storage
3. `/bubble` - Workspace bubbles
4. `/help_unified` - Unified help

### 4.2 Example (Anti-Pattern)

**File**: `isaac/commands/machine/run.py` (excerpt)

```python
def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    action = sys.argv[1]

    if action == 'register':
        # Parse remaining args manually
        hostname = None
        ip_address = None
        port = 22

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--hostname':
                hostname = sys.argv[i+1]
                i += 2
            elif sys.argv[i] == '--ip-address':
                ip_address = sys.argv[i+1]
                i += 2
            elif sys.argv[i] == '--port':
                port = int(sys.argv[i+1])
                i += 2
            else:
                i += 1

        # ... 50 more lines of manual parsing ...
```

### 4.3 Strengths

❓ **Simple for trivial cases?** - Direct access to args

### 4.4 Weaknesses

❌ **No validation** - Type errors at runtime
❌ **No help generation** - Must write manually
❌ **Error prone** - Index out of bounds errors
❌ **No default values** - Must handle missing args
❌ **Hard to maintain** - Adding new flags is tedious

### 4.5 When to Use

**Use Pattern F when:**
- ❌ **NEVER** - Always use argparse instead

**Recommendation**: Migrate all Pattern F commands to argparse (Pattern A).

---

## 8. PATTERN G: Placeholder/Stub

### 4.1 Description

**Non-functional** commands that exist but don't work.

**Commands:**
1. `/backup` - Returns placeholder JSON
2. `/list` - Returns placeholder JSON
3. `/claude-artifacts` - Empty stub (no implementation)
4. `/openai-vision` - Empty stub (no implementation)

### 4.2 Example

**File**: `isaac/commands/backup/run.py` (excerpt)

```python
def main():
    """Main entry point for backup command"""
    payload = json.loads(sys.stdin.read())
    args = payload.get("args", {})

    # Placeholder implementation
    target = args.get("target", "all")

    output = f"Backup feature coming soon. Target: {target}"

    print(json.dumps({
        "ok": True,
        "kind": "text",
        "stdout": output,
        "meta": {"placeholder": True}
    }))
```

### 4.3 Recommendation

**For placeholder commands:**
- ❌ **Delete** if no plans to implement
- ⏸️ **Document** in roadmap if planned
- ✅ **Implement** if critical

**For empty stubs:**
- ❌ **Delete immediately** - No value

---

## 9. BEST PRACTICES MATRIX

### 9.1 Implementation Best Practices

| Practice | Pattern A | Pattern B | Pattern C | Pattern D | Pattern E | Pattern F | Pattern G |
|----------|-----------|-----------|-----------|-----------|-----------|-----------|-----------|
| **Use argparse** | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | N/A |
| **JSON envelope output** | ✅ | ✅ | ✅ | ❌ | Partial | ❌ | Partial |
| **Comprehensive help** | ✅ | Varies | Varies | ❌ | ❌ | ❌ | N/A |
| **Examples in help** | ✅ | Varies | Varies | ❌ | ❌ | ❌ | N/A |
| **Error handling** | ✅ | ✅ | ✅ | Partial | Partial | Partial | N/A |
| **Type validation** | ✅ | Manual | Manual | Manual | Manual | ❌ | N/A |
| **Standalone runnable** | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | N/A |
| **Dispatcher compatible** | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ | Partial |
| **Testable** | ✅ | ✅ | Partial | Partial | ❌ | ❌ | N/A |
| **Maintainable** | ✅ | ✅ | Partial | ✅ | ❌ | ❌ | N/A |

### 9.2 Recommended Patterns by Use Case

| Use Case | Recommended Pattern | Alternative | Avoid |
|----------|---------------------|-------------|-------|
| **User-facing file command** | Pattern A (argparse + Tool) | - | Pattern F |
| **Internal system command** | Pattern B (stdin-json) | Pattern A | Pattern E |
| **Complex multi-feature command** | Pattern A with subparsers | Pattern D | Pattern C |
| **Simple query command** | Pattern B (stdin-json) | Pattern A | Pattern F |
| **AI integration command** | Pattern A (argparse) | - | Pattern E |

---

## 10. ANTI-PATTERNS TO ELIMINATE

### 10.1 Anti-Pattern #1: Multiple Input Methods

**Problem**: Commands that accept both stdin-json AND sys.argv
**Examples**: `/ask`, `/msg`, `/tasks`
**Impact**: Complex, fragile, hard to test

**Fix**:
```python
# Bad
if not sys.stdin.isatty():
    try:
        data = json.loads(sys.stdin.read())
        if 'kind' in data:
            # blob mode
        elif 'manifest' in data:
            # dispatcher mode
    except:
        # plain text mode
else:
    # sys.argv mode

# Good (Pattern A)
parser = argparse.ArgumentParser()
args = parser.parse_args()
```

### 10.2 Anti-Pattern #2: Manual Flag Parsing

**Problem**: Custom loops to parse `--flag value`
**Examples**: `/machine`, `/images`, `/bubble`
**Impact**: Bug-prone, no validation, no help

**Fix**:
```python
# Bad
i = 0
while i < len(sys.argv):
    if sys.argv[i] == '--hostname':
        hostname = sys.argv[i+1]
        i += 2

# Good
parser = argparse.ArgumentParser()
parser.add_argument('--hostname', required=True)
args = parser.parse_args()
hostname = args.hostname
```

### 10.3 Anti-Pattern #3: Multiple Output Formats

**Problem**: Same command returns different formats
**Examples**: `/ask` (blob/envelope/plain)
**Impact**: Inconsistent, hard to consume

**Fix**:
```python
# Bad
if return_blob:
    print(json.dumps({"kind": "text", "content": response}))
else:
    print(json.dumps({"ok": True, "stdout": response}))

# Good
print(json.dumps({"ok": True, "stdout": response}))  # Always envelope
```

### 10.4 Anti-Pattern #4: Placeholder Implementations

**Problem**: Commands that don't work
**Examples**: `/backup`, `/list`, `/claude-artifacts`, `/openai-vision`
**Impact**: Confusing for users, wasted effort

**Fix**: Delete or implement fully

---

## 11. MIGRATION GUIDELINES

### 11.1 Pattern F → Pattern A Migration

**Steps to migrate manual sys.argv to argparse:**

1. **Identify all flags and arguments**
   ```python
   # Before: Manual parsing
   action = sys.argv[1]
   hostname = None
   for i in range(2, len(sys.argv)):
       if sys.argv[i] == '--hostname':
           hostname = sys.argv[i+1]
   ```

2. **Create argparse structure**
   ```python
   # After: argparse
   parser = argparse.ArgumentParser(description='Machine registry')
   parser.add_argument('action', choices=['register', 'unregister', 'list'])
   parser.add_argument('--hostname', required=True, help='Machine hostname')
   args = parser.parse_args()
   ```

3. **Add help text and examples**
   ```python
   parser = argparse.ArgumentParser(
       description='Machine registry',
       epilog="""
   Examples:
     /machine register --hostname server1
     /machine list
     /machine unregister --machine-id abc123
       """
   )
   ```

4. **Add JSON envelope output**
   ```python
   if not sys.stdout.isatty():
       envelope = {"ok": True, "stdout": result}
       print(json.dumps(envelope))
   ```

5. **Test thoroughly**
   - All previous invocations still work
   - New invocations with argparse work
   - Help text displays correctly
   - JSON envelope works

### 11.2 Pattern E → Pattern A Migration

**Steps to simplify hybrid commands:**

1. **Identify all input modes**
   ```python
   # Before: Multiple modes
   if not sys.stdin.isatty():
       data = json.loads(sys.stdin.read())
       if 'kind' in data:
           # blob mode
       elif 'manifest' in data:
           # dispatcher mode
   else:
       # sys.argv mode
   ```

2. **Choose single primary mode** (usually Pattern A)

3. **Deprecate other modes** with warnings

4. **Update documentation**

5. **Provide migration period** (1 release cycle)

### 11.3 Pattern D → Pattern D+ Migration

**Steps to improve command class delegates:**

1. **Keep command class** (it's fine for complex commands)

2. **Add argparse in run.py**
   ```python
   # run.py
   parser = argparse.ArgumentParser()
   # ... add arguments ...
   args = parser.parse_args()

   command = LearnCommand()
   command.execute(args)
   ```

3. **Add JSON envelope output**
   ```python
   # In command class
   def execute(self, args):
       result = self._execute_internal(args)

       # Add envelope output
       if not sys.stdout.isatty():
           envelope = {"ok": True, "stdout": result}
           print(json.dumps(envelope))
   ```

---

## CONCLUSION

**Summary of Recommendations:**

1. ✅ **Use Pattern A (argparse + Tool)** for all new user-facing commands
2. ✅ **Use Pattern B (stdin-json)** for internal/dispatcher-only commands
3. ⚠️ **Migrate Pattern C** commands to A or B
4. ⚠️ **Improve Pattern D** commands with envelope output
5. ❌ **Eliminate Pattern E** (hybrid) - too complex
6. ❌ **Eliminate Pattern F** (manual parsing) - use argparse
7. ❌ **Remove Pattern G** (placeholders) - delete or implement

**Impact of Standardization:**
- ⬆️ Consistency: From 20% to 100% compliant
- ⬆️ Maintainability: Single pattern to learn
- ⬆️ Testability: Standard patterns are easier to test
- ⬆️ User Experience: Consistent help and error messages
- ⬇️ Complexity: Eliminate custom parsers and hybrid modes

---

**End of Report**
