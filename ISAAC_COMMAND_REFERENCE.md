# ISAAC Command Reference
## Comprehensive Command Documentation

### Core Commands

#### `/ask` - AI Assistant Interface
**Status:** ✅ Implemented (with help pattern)

**Usage:**
```
/ask <question>                    - Ask a question
/ask --async <question>            - Ask asynchronously (returns message ID)
/ask --model <model> <question>    - Use specific AI model
/ask --help                        - Show this help
```

**Examples:**
```
/ask "write a python function"
/ask --async "analyze data" | /newfile report.md
/ask --model gpt-4 "complex analysis"
```

**Aliases:** `/query`, `/q`

**Notes:** For command execution, use natural language without `/ask` prefix

---

#### `/newfile` - File Creation with Templates
**Status:** ✅ Implemented

**Usage:**
```
/newfile <file>                    - Create file with automatic template
/newfile <file> --template <ext>   - Create with specific template
/newfile <file> --content <text>   - Create with inline content
/newfile <file> --force            - Overwrite existing files
/newfile --list-templates          - Show available templates
/newfile --set-template <ext> <content> - Set template for extension
/newfile --help                    - Show this help
```

**Examples:**
```
/newfile script.py
/newfile notes.txt --content "My notes"
/newfile report.md --template .md
```

**Notes:** Supports piping content from other commands

---

#### `/messages` - Internal Messaging System
**Status:** 🎯 Designed (ready for implementation)

**Usage:**
```
/messages                           - View unread messages
/messages --all                     - View all messages
/messages --status                  - Show message counts
/messages --clear                   - Clear read messages
/messages --clear-all               - Clear all messages (dangerous)
/messages send <agent> <message>    - Send message to agent
/messages send --task <agent> <msg> - Send as executable task
/messages send --priority <level>   - Set message priority
```

**Examples:**
```
/messages
/messages --all --limit 5
/messages send daniel "review this code"
/messages send sarah "analyze data" --task --priority high
```

**Aliases:** `/msg`

**Notes:** Central hub for all ISAAC messaging operations

---

#### `/email` - External Email Integration
**Status:** 🎯 Designed (ready for implementation)

**Usage:**
```
/email send <address> <message>     - Send email
/email send --subject <subj> <addr> <msg> - Send with subject
/email send --attach <file>         - Attach file
/email fetch                        - Get emails as messages
/email check --unread               - Check for new emails
/email check --since <time>         - Check recent emails
/email inbox                        - Show email inbox
```

**Examples:**
```
/email send user@domain.com "Report complete"
/email fetch
/analyze data | /email team@company.com --subject "Analysis Results"
```

**Notes:** Bridges external email with ISAAC messaging system

---

### System Commands

#### `/config` - Configuration Management
**Status:** 📝 Mentioned (needs implementation)

**Usage:**
```
/config                             - Show current configuration
/config <section> <key> <value>     - Set configuration value
/config <section>                   - Show section configuration
/config --reset <section>           - Reset section to defaults
/config --export                    - Export configuration
/config --import <file>             - Import configuration
```

**Examples:**
```
/config
/config ai model gpt-4
/config ui theme dark
/config --reset ai
```

**Notes:** Manages all ISAAC configuration settings

---

#### `/alias` - Unix Command Translation
**Status:** ✅ Implemented

**Usage:**
```
/alias --list                       - List all available aliases
/alias --show <command>             - Show details for specific Unix command
/alias --enable                     - Enable Unix alias translation
/alias --disable                    - Disable Unix alias translation
/alias --add <unix_cmd> <ps_cmd>    - Add custom alias mapping
/alias --remove <unix_cmd>          - Remove custom alias
```

**Examples:**
```
/alias --list
/alias --show ls
/alias --enable
/alias --add ll "ls -la"
```

**Notes:** Translates Unix commands to PowerShell equivalents on Windows

---

#### `/backup` - Data Backup
**Status:** ✅ Implemented

**Usage:**
```
/backup                             - Backup all data (config, session, files)
/backup --target config             - Backup configuration only
/backup --target session            - Backup session data only
/backup --target all                - Backup everything (default)
```

**Examples:**
```
/backup
/backup --target config
```

**Notes:** Creates timestamped backup archives in ~/.isaac/backups/

---

#### `/restore` - Data Restore
**Status:** ✅ Implemented

**Usage:**
```
/restore --file <backup_file>        - Restore from specific backup file
```

**Examples:**
```
/restore --file config_backup_2025-10-23.zip
/restore --file session_backup.zip
```

**Notes:** Lists available backups if no file specified

---

#### `/sync` - Cloud Synchronization
**Status:** ✅ Implemented

**Usage:**
```
/sync                               - Force sync queued commands to cloud
/sync --dry-run                     - Show what would be synced (no actual sync)
/s                                  - Short alias for sync
```

**Examples:**
```
/sync
/sync --dry-run
```

**Notes:** Forces immediate synchronization of command queue to cloud storage

#### `/status` - System Status
**Status:** ✅ Implemented

**Usage:**
```
/status                             - Show system status
/status --verbose                   - Show detailed status
```

**Examples:**
```
/status
/status --verbose
```

**Notes:** Provides system health information with optional verbose details

---

#### `/help` - Help System
**Status:** 📝 Mentioned (needs implementation)

**Usage:**
```
/help                               - Show general help
/help <command>                     - Show help for specific command
/help --all                         - Show all available commands
/help --search <term>               - Search help for term
```

**Examples:**
```
/help
/help /newfile
/help --search template
```

**Notes:** Central help system for all commands

---

### Session Management

#### `/start` - Launch ISAAC
**Status:** 📝 Mentioned (existing functionality)

**Usage:**
```
isaac /start                        - Launch ISAAC shell
isaac /start --config <file>        - Start with specific config
isaac /start --offline              - Start in offline mode
```

**Notes:** Launches the permanent ISAAC shell

---

#### `/exit` - Exit Session
**Status:** 📝 Mentioned (existing functionality)

**Usage:**
```
/exit                               - Exit ISAAC shell
/quit                               - Alias for exit
```

**Notes:** Gracefully terminates the ISAAC session

---

### Advanced Commands

#### `/mine` - Data Mining Operations
**Status:** 📝 Mentioned (needs implementation)

**Usage:**
```
/mine <path>                        - Mine data from path
/mine <path> --type <format>        - Specify data type
/mine <path> --query <question>     - Ask question about data
/mine --list-sources                - Show available data sources
```

**Examples:**
```
/mine ./logs
/mine ./data --type json --query "find errors"
/mine --list-sources
```

**Notes:** Extracts and analyzes data from various sources

---

### Natural Language Commands

#### Direct AI Commands (no prefix)
**Status:** ✅ Core functionality

**Usage:**
```
<natural language query>            - Execute command via AI
"find large files"                  - AI translates to shell command
"create a backup"                   - AI generates backup commands
```

**Examples:**
```
find files larger than 100MB
show me the disk usage
create a backup of my documents
```

**Notes:** ISAAC's primary interface - natural language to shell commands

---

### Command Architecture Notes

#### Standard Patterns
- **Help-first behavior:** All commands show help when invoked without arguments
- **JSON envelope:** Commands return structured JSON responses
- **Pipe support:** All commands support piping input/output
- **Error handling:** Consistent error response format
- **Session integration:** All commands work with session management

#### Response Format
```json
{
  "ok": true|false,
  "stdout": "command output",
  "error": {
    "code": "ERROR_TYPE",
    "message": "human readable message"
  },
  "meta": {
    "command": "/command_name"
  }
}
```

#### Pipe Format
```json
{
  "kind": "text|error",
  "content": "pipe content",
  "meta": {
    "command": "source_command",
    "timestamp": "2025-10-23T..."
  }
}
```

#### Configuration Structure
```json
{
  "ai": {
    "model": "gpt-4",
    "timeout": 30
  },
  "ui": {
    "theme": "dark",
    "prompt_style": "minimal"
  },
  "messages": {
    "max_age_days": 7,
    "auto_clear": true
  }
}
```

---

### Implementation Priority

**Phase 1 (High Priority):**
- `/messages` - Core messaging infrastructure
- `/config` - Configuration management
- `/status` - System monitoring

**Phase 2 (Medium Priority):**
- `/email` - External integration
- `/help` - Documentation system
- `/mine` - Data operations

**Phase 3 (Lower Priority):**
- Advanced features and refinements
- Additional aliases and shortcuts

---

### Quality Gates

**All commands must:**
- ✅ Follow help-first pattern
- ✅ Support piping (input/output)
- ✅ Return consistent JSON format
- ✅ Handle errors gracefully
- ✅ Integrate with session management
- ✅ Include comprehensive help text
- ✅ Support `--help` flag
- ✅ Have appropriate aliases where applicable

---

*Last updated: October 23, 2025*
*This document serves as the authoritative reference for ISAAC command implementation*</content>
<parameter name="filePath">c:\Projects\Isaac-1\ISAAC_COMMAND_REFERENCE.md