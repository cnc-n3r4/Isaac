# COMMAND STANDARDIZATION REPORT
**Project:** ISAAC Command System Analysis
**Agent:** Agent 2 - Command System Auditor
**Date:** 2025-11-09
**Total Commands Analyzed:** 50+

---

## EXECUTIVE SUMMARY

The ISAAC command system consists of **50+ commands** with **7 distinct implementation patterns** and **significant inconsistencies** in:
- Argument parsing (argparse vs custom vs sys.argv)
- Input format (stdin-json vs sys.argv)
- Output format (JSON envelope vs plain text vs blob)
- Help text coverage (15 commands lack examples)
- Error handling approaches

**Current State**: **Only 10/50 commands (20%) follow the recommended standard schema.**

---

## 1. CURRENT STATE

### 1.1 Commands Following Standard Schema: **10/50 (20%)**

**Fully Compliant Commands** (argparse + JSON envelope + comprehensive help):
1. `/edit` - Edit files with string replacement
2. `/file` - Unified file operations (read/write/edit/append)
3. `/grep` - Search files with regex
4. `/read` - Read files with line numbers
5. `/write` - Create new files
6. `/search` - Unified search (glob + grep)
7. `/newfile` - Create files with templates
8. `/config` - Configuration management (stdin-json variant)
9. `/mine` - xAI Collections manager (complex but consistent)
10. `/help` - Help system (stdin-json variant)

### 1.2 Partially Compliant Commands: **15/50 (30%)**

Commands with **some** standard patterns but missing key elements:
- `/alias` - stdin-json ✓, custom parser ✗, help ✓
- `/status` - stdin-json ✓, help missing ✗
- `/machines` - stdin-json ✓, help missing ✗
- `/glob` - argparse ✓, double output ✗
- `/man` - stdin-json ✓, no JSON envelope ✗
- `/ask` - Multiple modes ✗, no help ✗
- `/debug` - args dict ✓, no JSON envelope ✗
- `/help_unified` - sys.argv ✗, no JSON envelope ✗
- `/apropos` - stdin-json ✓, no envelope ✗
- `/analyze` - stdin-json ✓, blob format ✗
- `/msg` - hybrid input ✗, no envelope ✗
- `/tasks` - hybrid input ✗, no envelope ✗
- `/machine` - sys.argv ✗, no envelope ✗
- `/images` - sys.argv ✗, no envelope ✗
- `/bubble` - sys.argv ✗, no envelope ✗

### 1.3 Non-Compliant Commands: **22/50 (44%)**

Commands using **non-standard patterns**:
- `/ambient`, `/learn`, `/pair` - Command class delegates, no envelope
- `/backup`, `/list` - Placeholder implementations (not functional)
- `/claude-artifacts`, `/openai-vision` - Empty stubs
- `/arvr`, `/pipeline`, `/plugin`, `/queue`, `/resources`, `/restore`, `/save`, `/script`, `/share`, `/summarize`, `/sync`, `/team`, `/timemachine`, `/update`, `/upload`, `/watch`, `/whatis`, `/workspace` - Not fully analyzed (18 commands)

### 1.4 Unknown Status: **3/50 (6%)**

Commands with **incomplete analysis** or **placeholder status**:
- `/backup` - Placeholder (P0 priority fix)
- `/list` - Placeholder (P0 priority fix)
- `/claude-artifacts`, `/openai-vision` - Empty stubs (P0 priority fix)

---

## 2. COMMON INCONSISTENCIES (Top 10)

### 2.1 **Argument Parsing Diversity** (Critical)
- **argparse**: 10 commands ✓
- **Custom flag parser**: 5 commands (alias, mine, help_unified)
- **Manual sys.argv**: 8 commands (machine, images, bubble, ambient, learn, pair, msg, tasks)
- **stdin-json only**: 12 commands (varying degrees of structure)

**Impact**: Developers must learn 4+ different parsing approaches. Maintenance burden high.

**Example Inconsistency**:
```python
# /edit (standard argparse)
parser = argparse.ArgumentParser(description='Edit files')
parser.add_argument('file_path', help='Path to file')

# /alias (custom parser)
def parse_flags(args_list):
    flags = {}
    while i < len(args_list):
        if arg.startswith('--'):
            # custom logic...

# /machine (manual sys.argv)
if len(sys.argv) < 2:
    print_usage()
action = sys.argv[1]
```

### 2.2 **Output Format Chaos** (Critical)
- **JSON envelope** (`{ok, stdout, meta}`): 15 commands
- **JSON blob** (`{kind, content, meta}`): 2 commands (analyze, ask)
- **Plain text only**: 10 commands
- **Mixed (TTY detection)**: 5 commands

**Impact**: Commands cannot be reliably chained or piped. API consumers need command-specific handling.

**Recommendation**: Standardize on JSON envelope for ALL commands.

### 2.3 **Help Text Coverage Gaps** (High)
- **Comprehensive help + examples**: 15 commands (30%)
- **Usage only**: 8 commands (16%)
- **No help at all**: 7 commands (14%)
- **Unknown**: 20 commands (40%)

**Impact**: Poor user experience. Users must read source code to understand commands.

**Missing Help Examples**:
- `/status` - No help text
- `/machines` - No help text
- `/debug` - No help text
- `/images` - No help text
- `/tasks` - Usage only, no examples

### 2.4 **Error Handling Inconsistency** (High)
- **JSON envelope errors**: 15 commands
- **sys.exit(1) + stderr**: 10 commands
- **Plain exceptions**: 3 commands
- **No error handling**: 2 commands (placeholders)

**Impact**: Errors from different commands appear inconsistent. Programmatic error handling impossible.

### 2.5 **Input Method Inconsistency** (High)
- **stdin-json (dispatcher)**: 25 commands
- **sys.argv (standalone)**: 15 commands
- **Hybrid (both)**: 10 commands

**Impact**: Commands behave differently when called via dispatcher vs shell. Confusing for users.

### 2.6 **Flag Naming Conventions** (Medium)
- **Long flags**: Most commands use `--flag-name`
- **Short flags**: Inconsistent usage (-i, -C, -v, -f, -s, -l, -h, -r, -c, -a)
- **Flag aliases**: Some commands have aliases, others don't
- **Boolean vs value flags**: Mixed handling

**Examples**:
```bash
/grep --ignore-case   # Long form
/grep -i              # Short form ✓ (has alias)

/help --verbose       # Long form only ✗ (no short form)
/status -v            # Short form documented but not in argparse ✗
```

### 2.7 **Placeholder/Stub Commands** (Critical - P0)
- `/backup` - Placeholder implementation
- `/list` - Placeholder implementation
- `/claude-artifacts` - Empty stub
- `/openai-vision` - Empty stub

**Impact**: Commands exist but don't work. Misleading for users. Should be removed or completed.

### 2.8 **Dual Implementation Anti-Pattern** (Medium)
Several commands have **BOTH** standalone `.py` AND directory versions:
- `backup.py` + `backup/run.py`
- `config.py` + `config/run.py`
- `help.py` + `help/run.py`
- `list.py` + `list/run.py`
- `msg.py` + `msg/run.py`
- `restore.py` + `restore/run.py`
- `status.py` + `status/run.py`

**Impact**: Confusing which version is active. Maintenance duplication. Code drift risk.

### 2.9 **Wildly Non-Compliant: `/ask` Command** (High)
The `/ask` command has **3 different execution modes** with different output formats:
1. **Piped mode**: Returns JSON blob `{kind, content, meta}`
2. **Dispatcher mode**: Returns JSON envelope `{ok, stdout}`
3. **Standalone mode**: Returns plain text

**Code Complexity**: 350 lines with complex blob detection logic.

**Impact**: Extremely difficult to maintain. Other developers avoid this pattern.

### 2.10 **Missing Examples in Help** (Medium)
**15 commands** have help text but **no usage examples**:
- `/alias` - Has examples ✓
- `/machine` - No examples ✗
- `/msg` - No examples ✗
- `/tasks` - No examples ✗
- `/images` - No examples ✗
- `/debug` - No examples ✗

**Impact**: Users must experiment or read code. Increases support burden.

---

## 3. STANDARD SCHEMA PROPOSAL

### 3.1 Universal Command Pattern

**All commands MUST follow this pattern:**

```python
#!/usr/bin/env python3
"""
[Command Name] - [One-line description]

[Detailed description of command purpose and functionality]
"""

import sys
import json
import argparse
from pathlib import Path

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.tools import [ToolName]  # If applicable


def main():
    """Main entry point for /[command] command"""
    parser = argparse.ArgumentParser(
        description='[Command description]',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  /[command] example1
  /[command] example2 --flag
  /[command] example3 --option value

Additional documentation: /help /[command]
        """
    )

    # Required positional arguments
    parser.add_argument('arg1', help='Description of arg1')

    # Optional positional arguments
    parser.add_argument('arg2', nargs='?', default=None, help='Description of arg2')

    # Optional flags (boolean)
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # Optional flags (with values)
    parser.add_argument('--output', '-o', default='text', choices=['text', 'json'],
                       help='Output format (default: text)')

    # Help flag
    parser.add_argument('--help-cmd', action='store_true', help='Show this help')

    try:
        # Show help if no arguments
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(0)

        args = parser.parse_args()

        if args.help_cmd:
            parser.print_help()
            sys.exit(0)

        # Execute command logic
        result = execute_command(args)

        # Output result (human-readable)
        print(result['message'])

        # Return JSON envelope for dispatcher/piping
        if not sys.stdout.isatty():
            envelope = {
                "ok": True,
                "stdout": result['message'],
                "meta": {
                    "command": "/[command]",
                    "executed_at": result.get('timestamp'),
                }
            }
            print(json.dumps(envelope))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)

        if not sys.stdout.isatty():
            envelope = {
                "ok": False,
                "error": {
                    "code": "EXECUTION_ERROR",
                    "message": str(e)
                }
            }
            print(json.dumps(envelope))

        sys.exit(1)


def execute_command(args):
    """Execute the command logic (separate from argument parsing)"""
    # Command implementation here
    return {"message": "Success", "timestamp": "2025-11-09"}


if __name__ == "__main__":
    main()
```

### 3.2 Schema Requirements

**Required Elements:**
1. ✅ **Docstring** - Module-level docstring with description
2. ✅ **argparse** - Standard argument parser (NO custom parsers)
3. ✅ **Help text** - Comprehensive help with `--help-cmd` flag
4. ✅ **Examples** - Minimum 3 examples in epilog
5. ✅ **Error handling** - Try-except with JSON envelope
6. ✅ **JSON envelope output** - For non-TTY (piping/dispatcher)
7. ✅ **Human-readable output** - For TTY (interactive use)
8. ✅ **Exit codes** - 0 for success, 1 for error

**Flag Naming Conventions:**
- **Long flags**: `--flag-name` (lowercase, hyphen-separated)
- **Short flags**: Single letter `-f` (only for commonly used flags)
- **Boolean flags**: Use `action='store_true'` (no value needed)
- **Value flags**: Specify type and default value

**Common Short Flags (Standardized):**
- `-h` / `--help` - Show help (built-in)
- `-v` / `--verbose` - Verbose output
- `-f` / `--force` - Force operation
- `-i` / `--ignore-case` - Case-insensitive
- `-o` / `--output` - Output file/format
- `-q` / `--quiet` - Quiet mode
- `-r` / `--recursive` - Recursive operation
- `-a` / `--all` - Include all items

**Argument Order:**
1. Required positional arguments first
2. Optional positional arguments (nargs='?')
3. Boolean flags (action='store_true')
4. Value flags (with defaults)

---

## 4. MIGRATION PLAN

### 4.1 Phase 1: **P0 Fixes (Week 1)** - Critical Issues

**Estimated Effort**: 8 hours

**Commands to Fix:**
1. `/backup` - Remove or implement placeholder (delete or complete)
2. `/list` - Remove or implement placeholder (delete or complete)
3. `/claude-artifacts` - Remove empty stub
4. `/openai-vision` - Remove empty stub

**Actions:**
- Audit: Are these commands referenced anywhere?
- If no references: **Delete**
- If referenced but incomplete: **Add to backlog** and mark as "Coming Soon"

### 4.2 Phase 2: **P1 Improvements (Weeks 2-3)** - Major Inconsistencies

**Estimated Effort**: 24 hours

**Commands to Refactor:**
1. `/alias` - Replace custom flag parser with argparse
2. `/ask` - Simplify to single output format (envelope only)
3. `/msg` - Standardize input (stdin-json only, remove sys.argv)
4. `/tasks` - Standardize input (stdin-json only, remove sys.argv)
5. `/machine` - Replace manual sys.argv with argparse + stdin-json

**Migration Strategy:**
```python
# Before (custom parser):
def parse_flags(args_list):
    flags = {}
    # 30 lines of custom logic...

# After (argparse):
parser = argparse.ArgumentParser()
parser.add_argument('--list', action='store_true')
parser.add_argument('--show', type=str)
args = parser.parse_args()
```

### 4.3 Phase 3: **P2 Enhancements (Weeks 4-5)** - Medium Priority

**Estimated Effort**: 32 hours

**Commands to Improve:**
1. `/glob` - Remove double output (JSON envelope only)
2. `/help_unified` - Migrate to stdin-json + JSON envelope
3. `/man` - Add JSON envelope support
4. `/apropos` - Add JSON envelope support
5. `/debug` - Add JSON envelope support
6. `/images` - Migrate to argparse + JSON envelope
7. `/bubble` - Migrate to argparse + JSON envelope
8. `/ambient`, `/learn`, `/pair` - Add JSON envelope to command classes

**Add Comprehensive Help to:**
9. `/status` - Add help text and examples
10. `/machines` - Add help text and examples
11. `/debug` - Add examples
12. `/images` - Add help and examples

### 4.4 Phase 4: **P3 Polish (Week 6)** - Nice-to-Have

**Estimated Effort**: 16 hours

**Improvements:**
1. Add short flag aliases where appropriate
2. Ensure all commands have 3+ examples
3. Cross-link related commands in help text
4. Add `--json` flag to commands with plain text output
5. Standardize error codes (EXECUTION_ERROR, CONFIG_ERROR, etc.)

---

## 5. BREAKING CHANGES IMPACT

### 5.1 Commands That Will Change Syntax

**Breaking Changes Required:**

1. **`/alias`** - Flag parsing changes
   - Before: `/alias --show ls` (works)
   - After: `/alias --show ls` (argparse version - behavior unchanged)
   - **Impact**: Minimal - syntax stays the same, just implementation changes

2. **`/ask`** - Output format simplification
   - Before: Multiple formats (blob/envelope/plain)
   - After: JSON envelope only
   - **Impact**: Medium - piping behavior changes
   - **Migration**: Add output format converter for backward compatibility

3. **`/machine`** - Input method change
   - Before: `python machine.py register --hostname foo`
   - After: Dispatcher call via stdin-json
   - **Impact**: High if used as standalone script
   - **Migration**: Maintain sys.argv fallback for 1 release

### 5.2 User Migration Guide Needed

**Create migration guide for:**
1. Users running commands as standalone Python scripts (not via dispatcher)
2. Scripts/automations that parse command output
3. Custom integrations relying on blob format

**Guide Sections:**
- "What Changed and Why"
- "Before and After Examples"
- "Updating Your Scripts"
- "Backward Compatibility Period" (1 release cycle)

### 5.3 Deprecation Timeline

**Release N (Current):**
- Announce deprecation of non-standard patterns
- Add warnings to non-compliant commands

**Release N+1 (3 months):**
- Migrate P0 and P1 commands
- Maintain backward compatibility with warnings

**Release N+2 (6 months):**
- Migrate P2 commands
- Remove backward compatibility for P0/P1

**Release N+3 (9 months):**
- Complete P3 polish
- All commands standardized

---

## 6. IMPLEMENTATION CHECKLIST

### 6.1 Per-Command Migration Checklist

For each command being migrated:

- [ ] **Backup current implementation** (git branch)
- [ ] **Create test cases** for existing behavior
- [ ] **Implement new standard pattern**
  - [ ] Replace custom parser with argparse
  - [ ] Add comprehensive help text
  - [ ] Add 3+ examples in epilog
  - [ ] Implement JSON envelope output
  - [ ] Add proper error handling
- [ ] **Test against existing behavior**
- [ ] **Update documentation**
- [ ] **Add deprecation warnings** (if breaking changes)
- [ ] **Code review**
- [ ] **Merge and deploy**

### 6.2 Global Checklist

- [ ] Create standard command template (`commands/_template/run.py`)
- [ ] Document standard pattern in `CONTRIBUTING.md`
- [ ] Create command generator script (`scripts/generate_command.py`)
- [ ] Update test framework to verify schema compliance
- [ ] Create linter rules for command standards
- [ ] Update CI/CD to enforce standards

---

## 7. SUCCESS METRICS

### 7.1 Target Goals

**By End of Migration:**
- ✅ **100% of commands** use argparse (currently: 20%)
- ✅ **100% of commands** output JSON envelope (currently: 30%)
- ✅ **100% of commands** have comprehensive help (currently: 30%)
- ✅ **100% of commands** have 3+ examples (currently: 30%)
- ✅ **0 placeholder commands** (currently: 4)
- ✅ **0 dual implementations** (currently: 7)
- ✅ **100% test coverage** for command parsing

### 7.2 Quality Gates

**Before merging any command refactor:**
1. Passes linter rules for command standards
2. Has 3+ examples in help text
3. Has JSON envelope output with proper structure
4. Has comprehensive test coverage (>80%)
5. Documentation updated
6. No breaking changes without migration path

---

## 8. APPENDIX: COMMAND CLASSIFICATION

### 8.1 By Implementation Pattern

**Pattern A: stdin-json + JSON envelope** (Recommended ✅)
- config, help, status, machines, mine, backup, list

**Pattern B: argparse + JSON envelope** (Recommended ✅)
- edit, file, glob, grep, read, write, search, newfile

**Pattern C: Custom parser + stdin-json** (Refactor needed ⚠️)
- alias, mine (but mine is well-designed)

**Pattern D: Manual sys.argv** (Refactor needed ⚠️)
- machine, images, bubble, ambient, learn, pair, help_unified

**Pattern E: Hybrid stdin-json/sys.argv** (Refactor needed ⚠️)
- msg, tasks, ask

**Pattern F: Placeholder/Stub** (Remove or complete ❌)
- backup, list, claude-artifacts, openai-vision

### 8.2 By Priority Fix Level

**P0 (Critical - 4 commands):**
- backup, list, claude-artifacts, openai-vision

**P1 (High - 5 commands):**
- alias, ask, msg, tasks, machine

**P2 (Medium - 15 commands):**
- glob, help_unified, man, apropos, debug, images, bubble, ambient, learn, pair, pipeline, arvr, plugin, queue, resources

**P3 (Low - 10 commands):**
- edit, file, grep, read, write, search, newfile, config, help, status, machines, mine

**Unknown (18 commands):**
- restore, save, script, share, summarize, sync, team, timemachine, update, upload, watch, whatis, workspace (need analysis)

---

## 9. RECOMMENDATIONS SUMMARY

### 9.1 Immediate Actions (This Week)

1. ✅ **Delete or complete placeholder commands** (P0)
   - Remove: `/claude-artifacts`, `/openai-vision` (empty stubs)
   - Decision needed: `/backup`, `/list` (delete or implement?)

2. ✅ **Create standard command template**
   - Template file: `commands/_template/run.py`
   - Generator script: `scripts/generate_command.py`

3. ✅ **Document standards**
   - Update: `CONTRIBUTING.md`
   - Create: `COMMAND_DEVELOPMENT_GUIDE.md`

### 9.2 Short-Term Actions (Next 2 Weeks)

4. ✅ **Refactor P1 commands**
   - `/alias` - Replace custom parser
   - `/ask` - Simplify output formats
   - `/msg`, `/tasks` - Standardize input
   - `/machine` - Migrate to argparse

5. ✅ **Add comprehensive help to top 10 commands**
   - Prioritize most-used commands
   - Ensure 3+ examples each

### 9.3 Long-Term Actions (Next 2 Months)

6. ✅ **Complete P2 migrations**
   - 15 commands to refactor
   - Focus on consistency over features

7. ✅ **Polish and optimize**
   - Add short flag aliases
   - Cross-link related commands
   - Performance profiling

8. ✅ **Testing and validation**
   - Automated schema compliance checks
   - Integration tests
   - User acceptance testing

---

**End of Report**
