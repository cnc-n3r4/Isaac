# ISAAC FILE PATH MASTER LIST

**Complete file reference for agent analysis**
**Total Python Files:** 314
**Last Updated:** 2025-11-09

---

## AGENT 1: CORE ARCHITECTURE FILES

### Entry Point & Main
```
isaac/__init__.py                              # Package init
isaac/__main__.py                              # Main entry point ⭐ START HERE
setup.py                                       # Package setup
requirements.txt                               # Dependencies
```

### Core System (isaac/core/)
```
isaac/core/__init__.py
isaac/core/command_router.py                   # Command routing ⭐ CRITICAL
isaac/core/session_manager.py                  # Session management ⭐ CRITICAL
isaac/core/boot_loader.py                      # System initialization ⭐ CRITICAL
isaac/core/key_manager.py                      # Authentication
isaac/core/tier_validator.py                   # Safety validation ⭐ CRITICAL
isaac/core/ai_translator.py                    # Natural language translation
isaac/core/flag_parser.py                      # Flag parsing
isaac/core/task_manager.py                     # Task management
isaac/core/context_manager.py                  # Context management
isaac/core/message_queue.py                    # Message queuing
isaac/core/pipe_engine.py                      # Pipeline execution
isaac/core/streaming_executor.py               # Streaming execution
isaac/core/agentic_orchestrator.py             # Agent orchestration
isaac/core/command_history.py                  # History tracking
isaac/core/file_watcher.py                     # File watching
isaac/core/workspace_integration.py            # Workspace integration
isaac/core/workspace_sessions.py               # Workspace sessions
isaac/core/aliases.py                          # Alias management
isaac/core/unix_aliases.py                     # Unix aliases
isaac/core/cli_command_router.py               # CLI routing
isaac/core/multifile_ops.py                    # Multi-file operations
isaac/core/unified_fs.py                       # Unified filesystem
isaac/core/change_queue.py                     # Change tracking
isaac/core/performance.py                      # Performance monitoring
isaac/core/sandbox_enforcer.py                 # Sandbox security
isaac/core/fallback_manager.py                 # Fallback handling
isaac/core/man_pages.py                        # Manual pages
isaac/core/session_manager_old.py              # Old session mgr (DELETE?)
isaac/core/env_config.py                       # Environment config
```

### Runtime System (isaac/runtime/)
```
isaac/runtime/__init__.py
isaac/runtime/dispatcher.py                    # Runtime dispatcher
isaac/runtime/manifest_loader.py               # Manifest loading
isaac/runtime/security_enforcer.py             # Runtime security
```

### Models & Data (isaac/models/)
```
isaac/models/__init__.py
isaac/models/preferences.py                    # User preferences
isaac/models/task_history.py                   # Task history
isaac/models/aiquery_history.py                # AI query history
```

### UI Layer (isaac/ui/)
```
isaac/ui/permanent_shell.py                    # Interactive shell ⭐
isaac/ui/input_handler.py
isaac/ui/splash.py
isaac/ui/_archived/                            # Archived UI (DELETE?)
```

---

## AGENT 2: COMMAND SYSTEM FILES

### Commands Directory (isaac/commands/)

**Total Command Directories:** 50+

#### File Operations Commands
```
isaac/commands/read/                           # Read files ⭐ PRIORITY 1
isaac/commands/write/                          # Write files ⭐ PRIORITY 1
isaac/commands/edit/                           # Edit files ⭐ PRIORITY 1
isaac/commands/file/                           # File operations ⭐ PRIORITY 1
isaac/commands/glob/                           # Pattern matching ⭐ PRIORITY 1
isaac/commands/grep/                           # Search files ⭐ PRIORITY 1
isaac/commands/newfile/                        # Create files ⭐ PRIORITY 1
isaac/commands/save/                           # Save operations
isaac/commands/upload/                         # Upload files
isaac/commands/watch/                          # Watch files
```

#### System Commands
```
isaac/commands/status/                         # System status ⭐ PRIORITY 1
isaac/commands/config/                         # Configuration ⭐ PRIORITY 1
isaac/commands/config.py                       # Config implementation
isaac/commands/help/                           # Help system ⭐ PRIORITY 1
isaac/commands/help_unified/                   # Unified help
isaac/commands/debug/                          # Debug utilities ⭐ PRIORITY 1
isaac/commands/update/                         # Update system ⭐ PRIORITY 1
isaac/commands/list/                           # List operations
isaac/commands/search/                         # Search command
isaac/commands/whatis/                         # What is command
isaac/commands/apropos/                        # Apropos command
isaac/commands/man/                            # Manual pages
```

#### AI Commands
```
isaac/commands/ask/                            # AI questions ⭐ PRIORITY 2
isaac/commands/analyze/                        # Code analysis ⭐ PRIORITY 2
isaac/commands/summarize/                      # Summarization ⭐ PRIORITY 2
isaac/commands/openai-vision/                  # OpenAI Vision ⭐ PRIORITY 2
isaac/commands/claude-artifacts/               # Claude integration ⭐ PRIORITY 2
isaac/commands/learn/                          # Learning system
isaac/commands/mine/                           # xAI Collections/RAG
```

#### Workspace & Project Commands
```
isaac/commands/workspace/                      # Workspace mgmt ⭐ PRIORITY 2
isaac/commands/backup/                         # Backup system ⭐ PRIORITY 2
isaac/commands/backup.py                       # Backup implementation
isaac/commands/restore/                        # Restore system ⭐ PRIORITY 2
isaac/commands/sync/                           # Synchronization ⭐ PRIORITY 2
isaac/commands/share/                          # Sharing features ⭐ PRIORITY 2
isaac/commands/machine/                        # Machine management
isaac/commands/machines/                       # Machines (plural)
```

#### Advanced Features
```
isaac/commands/pipeline/                       # Pipeline execution ⭐ PRIORITY 3
isaac/commands/bubble/                         # Bubble system ⭐ PRIORITY 3
isaac/commands/queue/                          # Queue management ⭐ PRIORITY 3
isaac/commands/tasks/                          # Task management ⭐ PRIORITY 3
isaac/commands/timemachine/                    # Time machine ⭐ PRIORITY 3
isaac/commands/team/                           # Team collab ⭐ PRIORITY 3
isaac/commands/pair/                           # Pair programming ⭐ PRIORITY 3
isaac/commands/script/                         # Scripting ⭐ PRIORITY 3
```

#### Specialized Commands
```
isaac/commands/ambient/                        # Ambient features ⭐ PRIORITY 3
isaac/commands/analytics/                      # Analytics ⭐ PRIORITY 3
isaac/commands/arvr/                           # AR/VR features ⭐ PRIORITY 3
isaac/commands/images/                         # Image processing ⭐ PRIORITY 3
isaac/commands/resources/                      # Resource management ⭐ PRIORITY 3
```

#### Miscellaneous Commands
```
isaac/commands/alias/                          # Alias command (see Agent 3)
isaac/commands/plugin/                         # Plugin management
```

**Note:** Each command directory typically contains:
- `run.py` - Main command implementation
- `__init__.py` - Module initialization
- `README.md` - Command documentation (sometimes)

---

## AGENT 3: ALIAS SYSTEM FILES

### Cross-Platform System (isaac/crossplatform/) ⭐ CORE FOCUS
```
isaac/crossplatform/                           # Main directory
isaac/crossplatform/__init__.py
isaac/crossplatform/api/                       # API integrations
isaac/crossplatform/bubbles/                   # Bubble system
isaac/crossplatform/cloud/                     # Cloud sync
isaac/crossplatform/mobile/                    # Mobile support
isaac/crossplatform/offline/                   # Offline mode
isaac/crossplatform/web/                       # Web interface
```

### Shell Adapters (isaac/adapters/) ⭐ CRITICAL
```
isaac/adapters/__init__.py
isaac/adapters/base_adapter.py                 # Base adapter class ⭐
isaac/adapters/bash_adapter.py                 # Linux/Mac adapter ⭐ START HERE
isaac/adapters/powershell_adapter.py           # Windows adapter ⭐ START HERE
isaac/adapters/shell_detector.py               # Platform detection ⭐
```

### Alias Command
```
isaac/commands/alias/                          # Alias command implementation ⭐
```

### Core Alias Files
```
isaac/core/aliases.py                          # Core alias system ⭐
isaac/core/unix_aliases.py                     # Unix-specific aliases ⭐
```

---

## AGENT 4: DOCUMENTATION FILES

### Root Markdown Files (41 total)

#### Primary User Documentation (KEEP)
```
README.md                                      # Main readme ⭐
LICENSE                                        # License file ⭐
OVERVIEW.md                                    # Project overview
QUICK_START.md                                 # Quick start guide ⭐
HOW_TO_GUIDE.md                                # User guide
COMPLETE_REFERENCE.md                          # Complete reference
DOCUMENTATION_INDEX.md                         # Documentation index
```

#### Setup & Installation (REVIEW)
```
SETUP_COMPLETE.md                              # Setup completion
WINDOWS_SETUP.md                               # Windows-specific setup
CROSS_PLATFORM_DEV_GUIDE.md                    # Cross-platform dev guide
```

#### Command & System Reference (REVIEW)
```
ISAAC_COMMAND_REFERENCE.md                     # Command reference ⭐
ISAAC_COMMAND_SYSTEM_ANALYSIS.md               # Command system analysis
ALIAS_QUICK_REFERENCE.md                       # Alias quick reference
ALIAS_SYSTEM_ANALYSIS.md                       # Alias system analysis
```

#### AI & Features (REVIEW)
```
AI_ROUTING_BUILD_SUMMARY.md                    # AI routing summary
QUICK_START_AI.md                              # AI quick start
LEARNING_SYSTEM_SUMMARY.md                     # Learning system
PLUGIN_ARCHITECTURE_ANALYSIS.md                # Plugin architecture
PLUGIN_SYSTEM_QUICK_REFERENCE.md               # Plugin quick reference
PLUGIN_SYSTEM_SUMMARY.txt                      # Plugin summary
```

#### Analysis & Audits (INTERNAL - REVIEW)
```
ANALYSIS_FILES_README.md                       # Analysis files index
ANALYSIS_INDEX.md                              # Analysis index
AUDIT_DETAILED_REPORT.txt                      # Detailed audit report
AUDIT_EXECUTIVE_SUMMARY.md                     # Executive summary
AUDIT_QUICK_SUMMARY.txt                        # Quick summary
CODE_QUALITY_AUDIT_2025.md                     # Code quality audit
HOUSEKEEPING_REPORT.md                         # Housekeeping report
HOUSEKEEPING_SUMMARY.txt                       # Housekeeping summary
PERFORMANCE_ANALYSIS.md                        # Performance analysis
PERFORMANCE_QUICK_REFERENCE.txt                # Performance reference
SECURITY_ANALYSIS.md                           # Security analysis
SECURITY_SUMMARY.md                            # Security summary
VULNERABILITY_DETAILS.md                       # Vulnerability details
ISAAC_CLAUDE_CODE_ANALYSIS.md                  # Claude Code analysis
ISAAC_COMPREHENSIVE_ANALYSIS_EXECUTIVE_SUMMARY.md  # Comprehensive analysis
```

#### Project Tracking (INTERNAL - LIKELY OBSOLETE)
```
CLEANUP_PLAN.md                                # Cleanup plan
CLEANUP_SUMMARY.md                             # Cleanup summary
PHASE_3_5_TODO.md                              # Phase 3.5 TODO
PHASE_3_COMPLETE.md                            # Phase 3 complete
PHASE_5_5_SUMMARY.md                           # Phase 5.5 summary
IMPLEMENTATION_SUMMARY.md                      # Implementation summary
MSG_FEATURE_COMPLETE.md                        # MSG feature complete
NAS_SETUP_COMPLETE.md                          # NAS setup complete
GITHUB_COMPARISON.md                           # GitHub comparison
```

#### Miscellaneous (REVIEW)
```
proposal.md                                    # Project proposal
sunday_task.md                                 # Sunday task (current task)
```

#### New Documentation (Created by this analysis)
```
AGENT_EXECUTION_PLAN.md                        # This analysis plan
AGENT_QUICK_REFERENCE.md                       # Quick reference
FILE_PATH_MASTER_LIST.md                       # This file
```

---

## AGENT 5: DEAD CODE HUNTER FILES

### Full Codebase Scan
**Target:** All 314 .py files in isaac/

### Test Files in Root (Priority Audit)
```
test_agentic_orchestrator.py                   # Agent orchestration tests
test_agentic_workflow_integration.py           # Workflow integration tests
test_ai_router.py                              # AI router tests
test_ai_router_phase3.py                       # AI router phase 3 tests
test_ai_routing_config.py                      # AI routing config tests
test_batch.py                                  # Batch tests
test_collections.py                            # Collections tests
test_command_consolidation.py                  # Command consolidation tests
test_context_manager.py                        # Context manager tests
test_cost_optimizer.py                         # Cost optimizer tests
test_filtering.py                              # Filtering tests
test_message_queue.py                          # Message queue tests
test_monitoring_system.py                      # Monitoring system tests
test_msg_command.py                            # MSG command tests
test_msg_dispatcher.py                         # MSG dispatcher tests
test_phase6.py                                 # Phase 6 tests
test_phase7.py                                 # Phase 7 tests
test_phase_5_5.py                              # Phase 5.5 tests
test_phases8-10.py                             # Phases 8-10 tests
test_streaming_executor.py                     # Streaming executor tests
test_task_analyzer.py                          # Task analyzer tests
test_tool_registry.py                          # Tool registry tests
test_ui_integration.py                         # UI integration tests
test_workspace_sessions.py                     # Workspace sessions tests
```

### Other Root Files (Audit)
```
demo_agent.py                                  # Demo agent
temp_test.py                                   # Temporary test file (DELETE?)
```

### Organized Test Directory
```
tests/                                         # Organized tests directory
tests/unit/
tests/integration/
tests/fixtures/
tests/mocks/
```

### AI System (isaac/ai/)
```
isaac/ai/__init__.py
isaac/ai/provider_registry.py
isaac/ai/router.py                             # AI routing
isaac/ai/cost_optimizer.py                     # Cost optimization
isaac/ai/agent.py                              # AI agent
isaac/ai/tools.py                              # AI tools
isaac/ai/monitor.py                            # AI monitoring
```

### Tools System (isaac/tools/)
```
isaac/tools/__init__.py
isaac/tools/base.py                            # Base tool class
isaac/tools/registry.py                        # Tool registry
isaac/tools/file_ops.py                        # File operations
isaac/tools/shell_exec.py                      # Shell execution
isaac/tools/code_analysis.py                   # Code analysis
isaac/tools/code_search.py                     # Code search
```

### Support Modules (Scan All)
```
isaac/ambient/                                 # Ambient features
isaac/analytics/                               # Analytics
isaac/api/                                     # API integrations
isaac/arvr/                                    # AR/VR
isaac/bubbles/                                 # Bubble system
isaac/collections/                             # Collections
isaac/data/                                    # Data files
isaac/debugging/                               # Debugging
isaac/dragdrop/                                # Drag & drop
isaac/images/                                  # Image processing
isaac/integrations/                            # Integrations
isaac/learning/                                # Learning system
isaac/memory/                                  # Memory management
isaac/monitoring/                              # Monitoring
isaac/nlscript/                                # NL scripting
isaac/orchestration/                           # Orchestration
isaac/pairing/                                 # Pair programming
isaac/patterns/                                # Patterns
isaac/pipelines/                               # Pipelines
isaac/plugins/                                 # Plugins
isaac/queue/                                   # Queue
isaac/resources/                               # Resources
isaac/scheduler/                               # Scheduler
isaac/team/                                    # Team features
isaac/timemachine/                             # Time machine
isaac/voice/                                   # Voice commands
```

---

## AGENT 6: SECURITY & TIER FILES

### Tier Definition Files ⭐ CRITICAL
```
isaac/data/                                    # Data directory (tier definitions)
isaac/data/*.json                              # Tier configuration files
isaac/data/*.txt                               # Tier data files
```

### Validation & Security Core ⭐ CRITICAL
```
isaac/core/tier_validator.py                   # Tier validation ⭐ START HERE
isaac/core/command_router.py                   # Command routing (validation entry)
isaac/core/sandbox_enforcer.py                 # Sandbox security
isaac/core/key_manager.py                      # Authentication
isaac/runtime/security_enforcer.py             # Runtime security
```

### Shell Adapters (Injection Risk) ⭐ CRITICAL
```
isaac/adapters/bash_adapter.py                 # Bash execution ⚠️ HIGH RISK
isaac/adapters/powershell_adapter.py           # PowerShell execution ⚠️ HIGH RISK
isaac/adapters/base_adapter.py                 # Base adapter
```

### Plugin Security
```
isaac/plugins/plugin_security.py               # Plugin sandboxing
isaac/plugins/plugin_registry.py               # Plugin validation
```

### Tool Execution (Security Review)
```
isaac/tools/shell_exec.py                      # Shell execution ⚠️ HIGH RISK
isaac/tools/file_ops.py                        # File operations ⚠️ MEDIUM RISK
```

### All Command Implementations (Tier Assignment Check)
```
isaac/commands/*/run.py                        # All command implementations
```

---

## DIRECTORY STATISTICS

```
Total Directories: ~90
Total Python Files: 314
Total Markdown Files: 41+
Total Test Files: 24 (root) + tests/ directory

By Category:
├── Core: ~25 files
├── Commands: 50+ directories, ~100+ files
├── Tools: ~10 files
├── AI: ~10 files
├── UI: ~5 files
├── Adapters: ~5 files
├── Plugins: ~10 files
├── Support Modules: ~150 files
└── Tests: ~24+ files
```

---

## FILE PRIORITIES FOR ANALYSIS

### P0 - Critical (Start Immediately)
```
isaac/__main__.py                              # Entry point
isaac/core/command_router.py                   # Command routing
isaac/core/session_manager.py                  # Session management
isaac/core/tier_validator.py                   # Safety validation
isaac/adapters/bash_adapter.py                 # Bash adapter
isaac/adapters/powershell_adapter.py           # PowerShell adapter
isaac/crossplatform/                           # Alias system
isaac/data/                                    # Tier definitions
```

### P1 - High Priority (Day 1)
```
isaac/core/*                                   # All core files
isaac/commands/*/run.py                        # Command implementations
isaac/ui/permanent_shell.py                    # Interactive shell
isaac/ai/router.py                             # AI routing
isaac/tools/*                                  # All tools
```

### P2 - Medium Priority (Day 2)
```
isaac/models/*                                 # Data models
isaac/runtime/*                                # Runtime system
isaac/plugins/*                                # Plugin system
All root test_*.py files                       # Test files
All root *.md files                            # Documentation
```

### P3 - Lower Priority (Day 3)
```
isaac/learning/*                               # Learning system
isaac/analytics/*                              # Analytics
isaac/monitoring/*                             # Monitoring
isaac/team/*                                   # Team features
Specialized feature directories                # AR/VR, voice, etc.
```

---

## USEFUL COMMANDS

### Count files by type
```bash
find isaac -name "*.py" | wc -l               # Count Python files
find isaac -name "*.md" | wc -l               # Count markdown files
find isaac -type d | wc -l                    # Count directories
```

### Find files by pattern
```bash
find isaac -name "*adapter*.py"               # Find adapters
find isaac -name "*router*.py"                # Find routers
find isaac -name "run.py"                     # Find command implementations
```

### Search for specific code
```bash
grep -r "shell=True" isaac/                   # Find security risks
grep -r "subprocess" isaac/                   # Find subprocess calls
grep -r "def execute" isaac/                  # Find execute methods
grep -r "class.*Command" isaac/               # Find command classes
```

### File size analysis
```bash
find isaac -name "*.py" -exec wc -l {} + | sort -rn | head -20
# Find largest Python files
```

---

## AGENT COORDINATION

### File Ownership
- **Agent 1** owns: isaac/core/, isaac/runtime/, isaac/models/, isaac/__main__.py
- **Agent 2** owns: isaac/commands/
- **Agent 3** owns: isaac/crossplatform/, isaac/adapters/, alias-related files
- **Agent 4** owns: All *.md files in root
- **Agent 5** owns: Full codebase scan (overlaps all agents)
- **Agent 6** owns: isaac/data/, validation files, security-critical files

### Shared Files (Multiple Agents)
These files are important to multiple agents:
```
isaac/core/command_router.py                   # Agents 1, 2, 6
isaac/adapters/*.py                            # Agents 1, 3, 6
isaac/core/tier_validator.py                   # Agents 1, 6
isaac/core/aliases.py                          # Agents 1, 3
```

**Coordination:** If multiple agents analyze the same file, compare findings during synthesis.

---

## QUICK NAVIGATION

Jump to agent-specific file lists:
- [Agent 1 Files](#agent-1-core-architecture-files)
- [Agent 2 Files](#agent-2-command-system-files)
- [Agent 3 Files](#agent-3-alias-system-files)
- [Agent 4 Files](#agent-4-documentation-files)
- [Agent 5 Files](#agent-5-dead-code-hunter-files)
- [Agent 6 Files](#agent-6-security--tier-files)

---

**This master list provides complete file path reference for all agents. Cross-reference with AGENT_EXECUTION_PLAN.md for detailed analysis requirements.**

**Last updated:** 2025-11-09
**Total files tracked:** 314 Python + 41 Markdown + support files
**Repository:** /home/user/Isaac/
