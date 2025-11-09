# Code Complexity Analysis

**Agent 5: Dead Code Hunter**

## Overall Statistics

- **Total files:** 310
- **Total lines of code:** 67,271
- **Total functions:** 3299
- **Total classes:** 459
- **Average LOC per file:** 217

## Complexity Issues Found

- **Functions >50 lines:** 275
- **Functions >10 parameters:** 1
- **High complexity functions (>10):** 168
- **Deeply nested code (>4 levels):** 149
- **Large classes (>500 lines):** 25

---

## Top 20 Most Complex Functions

Sorted by cyclomatic complexity:

| Rank | Function | File | Lines | Complexity | Params | Recommendation |
|------|----------|------|-------|------------|--------|----------------|
| 1 | `main` | `isaac/commands/msg/run.py:20` | 249 | 67 | 0 | URGENT: Refactor |
| 2 | `main` | `isaac/commands/config/run.py:30` | 124 | 54 | 0 | URGENT: Refactor |
| 3 | `route_command` | `isaac/core/command_router.py:317` | 280 | 43 | 2 | URGENT: Refactor |
| 4 | `_handle_dig` | `isaac/commands/mine/run.py:968` | 135 | 31 | 2 | URGENT: Refactor |
| 5 | `main` | `isaac/commands/tasks/run.py:20` | 134 | 30 | 0 | URGENT: Refactor |
| 6 | `format_full_debug_output` | `isaac/commands/debug/run.py:99` | 136 | 27 | 1 | URGENT: Refactor |
| 7 | `translate` | `isaac/core/ai_translator.py:98` | 151 | 27 | 2 | URGENT: Refactor |
| 8 | `run` | `isaac/commands/help_unified/run.py:318` | 67 | 26 | 2 | URGENT: Refactor |
| 9 | `main` | `isaac/commands/ask/run.py:67` | 183 | 26 | 0 | URGENT: Refactor |
| 10 | `_handle_pan` | `isaac/commands/mine/run.py:1224` | 70 | 25 | 2 | URGENT: Refactor |
| 11 | `execute_agentic_task_sync` | `isaac/core/agentic_orchestrator.py:123` | 101 | 25 | 2 | URGENT: Refactor |
| 12 | `main` | `isaac/commands/newfile/run.py:20` | 161 | 23 | 0 | URGENT: Refactor |
| 13 | `main` | `isaac/commands/workspace/run.py:70` | 143 | 23 | 0 | URGENT: Refactor |
| 14 | `main` | `isaac/commands/grep/run.py:17` | 116 | 23 | 0 | URGENT: Refactor |
| 15 | `execute` | `isaac/tools/code_search.py:61` | 120 | 22 | 7 | URGENT: Refactor |
| 16 | `execute` | `isaac/tools/file_ops.py:71` | 152 | 22 | 2 | URGENT: Refactor |
| 17 | `parse_args` | `isaac/runtime/dispatcher.py:60` | 92 | 22 | 3 | URGENT: Refactor |
| 18 | `get_detailed_status` | `isaac/commands/status/run.py:64` | 125 | 22 | 1 | URGENT: Refactor |
| 19 | `_handle_config_command` | `isaac/core/command_router.py:226` | 90 | 22 | 2 | URGENT: Refactor |
| 20 | `_format_man_page` | `isaac/core/man_pages.py:86` | 118 | 22 | 3 | URGENT: Refactor |

---

## Functions Exceeding 50 Lines

**Total:** 275

Top 10 longest:

| Function | File | Lines | Complexity |
|----------|------|-------|------------|
| `get_detailed_help` | `isaac/commands/help/run.py:117` | 599 | 1 |
| `_load_builtin_templates` | `isaac/nlscript/templates.py:130` | 286 | 1 |
| `route_command` | `isaac/core/command_router.py:317` | 280 | 43 |
| `main` | `isaac/commands/msg/run.py:20` | 249 | 67 |
| `_setup_routes` | `isaac/crossplatform/mobile/mobile_api.py:25` | 240 | 5 |
| `execute_task` | `isaac/ai/task_planner.py:38` | 212 | 20 |
| `_setup_routes` | `isaac/crossplatform/api/rest_api.py:27` | 212 | 4 |
| `chat` | `isaac/ai/router.py:224` | 193 | 14 |
| `_load_fix_templates` | `isaac/debugging/fix_suggester.py:47` | 190 | 1 |
| `_get_terminal_html` | `isaac/crossplatform/web/web_server.py:181` | 189 | 1 |

---

## Functions with >10 Parameters

**Total:** 1

- `create_plugin` in `isaac/plugins/plugin_devkit.py:169` - **11 parameters** (consider using a config object)

---

## Deeply Nested Code (>4 levels)

**Total:** 149

| Function | File | Max Nesting | Complexity | Recommendation |
|----------|------|-------------|------------|----------------|
| `main` | `isaac/commands/config/run.py:30` | 18 | 54 | Extract nested logic |
| `run` | `isaac/commands/team/team_command.py:37` | 18 | 20 | Extract nested logic |
| `main` | `isaac/commands/msg/run.py:20` | 14 | 67 | Extract nested logic |
| `execute` | `isaac/commands/analytics/analytics_command.py:21` | 14 | 17 | Extract nested logic |
| `execute` | `isaac/commands/pipeline/pipeline_command.py:27` | 12 | 14 | Extract nested logic |
| `execute` | `isaac/commands/bubble/run.py:23` | 11 | 13 | Extract nested logic |
| `execute` | `isaac/commands/pair/pair_command.py:46` | 11 | 13 | Extract nested logic |
| `_handle_config_command` | `isaac/core/command_router.py:226` | 11 | 22 | Extract nested logic |
| `get_input_with_advanced_features` | `isaac/ui/_archived/advanced_input.py:30` | 10 | 16 | Extract nested logic |
| `execute` | `isaac/commands/bubble/bubble_command.py:25` | 10 | 12 | Extract nested logic |
| `execute` | `isaac/commands/learn/learn_command.py:44` | 10 | 12 | Extract nested logic |
| `execute` | `isaac/commands/resources/resources_command.py:47` | 10 | 12 | Extract nested logic |
| `parse_args` | `isaac/runtime/dispatcher.py:60` | 9 | 22 | Extract nested logic |
| `main` | `isaac/commands/tasks/run.py:20` | 9 | 30 | Extract nested logic |
| `handle_command` | `isaac/commands/mine/run.py:303` | 9 | 16 | Extract nested logic |

---

## Large Classes (>500 lines)

**Total:** 25

- `MineHandler` in `isaac/commands/mine/run.py:21` - **1545 lines**, 45 methods (consider splitting responsibilities)
- `PatternLearner` in `isaac/patterns/pattern_learner.py:78` - **858 lines**, 39 methods (consider splitting responsibilities)
- `CommandRouter` in `isaac/core/command_router.py:14` - **794 lines**, 14 methods (consider splitting responsibilities)
- `EnhancedAntiPatternDetector` in `isaac/patterns/enhanced_anti_patterns.py:100` - **773 lines**, 33 methods (consider splitting responsibilities)
- `TerminalControl` in `isaac/ui/_archived/terminal_control.py:39` - **705 lines**, 44 methods (consider splitting responsibilities)
- `TeamCommand` in `isaac/commands/team/team_command.py:20` - **684 lines**, 21 methods (consider splitting responsibilities)
- `TestGenerator` in `isaac/debugging/test_generator.py:54` - **664 lines**, 22 methods (consider splitting responsibilities)
- `PatternDocumentationGenerator` in `isaac/patterns/pattern_documentation.py:66` - **651 lines**, 23 methods (consider splitting responsibilities)
- `LearnCommand` in `isaac/commands/learn/learn_command.py:23` - **640 lines**, 16 methods (consider splitting responsibilities)
- `PatternEvolutionEngine` in `isaac/patterns/pattern_evolution.py:75` - **629 lines**, 30 methods (consider splitting responsibilities)
- `CloudImageStorage` in `isaac/images/cloud_storage.py:55` - **622 lines**, 27 methods (consider splitting responsibilities)
- `PluginCommand` in `isaac/commands/plugin/plugin_command.py:11` - **598 lines**, 18 methods (consider splitting responsibilities)
- `VoiceShortcutManager` in `isaac/voice/voice_shortcuts.py:50` - **585 lines**, 25 methods (consider splitting responsibilities)
- `DashboardBuilder` in `isaac/analytics/dashboard_builder.py:42` - **580 lines**, 20 methods (consider splitting responsibilities)
- `DebugHistoryManager` in `isaac/debugging/debug_history.py:55` - **574 lines**, 15 methods (consider splitting responsibilities)
- `AIRouter` in `isaac/ai/router.py:20` - **561 lines**, 17 methods (consider splitting responsibilities)
- `PairCommand` in `isaac/commands/pair/pair_command.py:27` - **554 lines**, 17 methods (consider splitting responsibilities)
- `CommandDispatcher` in `isaac/runtime/dispatcher.py:12` - **534 lines**, 13 methods (consider splitting responsibilities)
- `ResourcesCommand` in `isaac/commands/resources/resources_command.py:19` - **532 lines**, 14 methods (consider splitting responsibilities)
- `SessionManager` in `isaac/core/session_manager.py:46` - **532 lines**, 25 methods (consider splitting responsibilities)
- `CostOptimizer` in `isaac/ai/cost_optimizer.py:23` - **527 lines**, 15 methods (consider splitting responsibilities)
- `WebServer` in `isaac/crossplatform/web/web_server.py:11` - **527 lines**, 7 methods (consider splitting responsibilities)
- `FixSuggester` in `isaac/debugging/fix_suggester.py:39` - **526 lines**, 15 methods (consider splitting responsibilities)
- `TaskAnalyzer` in `isaac/ai/task_analyzer.py:44` - **520 lines**, 16 methods (consider splitting responsibilities)
- `ReportExporter` in `isaac/analytics/report_exporter.py:21` - **511 lines**, 10 methods (consider splitting responsibilities)

---

## Refactoring Recommendations

### Priority Levels

- **P0 (Critical):** 26 functions with complexity >20
- **P1 (High):** 29 functions with complexity 15-20
- **P2 (Medium):** 113 functions with complexity 10-15

### General Guidelines

1. **Target complexity:** Keep cyclomatic complexity < 10
2. **Function length:** Aim for < 50 lines per function
3. **Parameters:** Use config objects for > 5 parameters
4. **Nesting:** Keep nesting depth < 4 levels
5. **Class size:** Split classes > 300 lines into smaller components

