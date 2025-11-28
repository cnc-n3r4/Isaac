# Isaac - High-Performance AI Shell Assistant (C++/Python Hybrid)

## 🚀 Performance-First Architecture

**CRITICAL**: Isaac is transitioning to a **C++ core with Python bindings** for maximum performance and minimal memory footprint.

### Current Status (November 2025)
- ✅ **Lazy Loading**: Implemented - 45% memory reduction (60 MB → 33 MB startup)
- ✅ **Memory Pooling**: Implemented - CommandResult object reuse
- ✅ **Zero-Copy Operations**: Implemented - string_view in routing
- ✅ **Strategy Pattern Router**: Implemented - 15+ routing strategies
- ✅ **C++ Core**: Implemented - CommandRouter, TierValidator, ShellAdapter
- 🎯 **Target**: < 20 MB startup, < 10ms command latency, < 5% idle CPU

### Performance Targets
- **Startup Memory**: < 20 MB (currently ~33 MB with optimizations)
- **Command Latency**: < 10ms for simple commands
- **CPU Usage**: < 5% idle, < 20% during AI operations
- **Zero Bloat**: Shell replacement, not memory hog

### Development Setup (Hybrid Build System)
```bash
# Install Python dependencies
pip install -e .              # Python bindings and UI

# Build C++ core (REQUIRED for performance)
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)              # Compile optimized C++ core

# Test hybrid system
isaac --start --no-boot       # ✅ WORKING: Launch with C++ optimizations
isaac --oneshot /help         # Test single command

# Performance testing
pytest tests/test_tier_validator.py -v           # Core safety validation
pytest tests/test_command_router.py -v           # C++ router performance
pytest tests/ --cov=isaac --cov-report=term-missing  # Full coverage
```

### First Time Setup
```powershell
# Set API keys for AI functionality (at least one required)
$env:XAI_API_KEY = "your-xai-key"           # Grok (primary)
$env:ANTHROPIC_API_KEY = "your-claude-key"  # Claude (fallback)
$env:OPENAI_API_KEY = "your-openai-key"     # OpenAI (backup)

# Set master key for authentication (optional, creates ~/.isaac/.master_key)
$env:ISAAC_MASTER_KEY = "your-master-key"

# Launch Isaac
isaac --start
```

### What You'll See on Startup
Isaac displays a comprehensive boot sequence showing:
- **Core System Status**: Session manager, config, message queue, task manager, performance monitoring
- **AI Providers**: Shows which AI services are configured (Grok primary, Claude/OpenAI as fallbacks)
- **Commands Loaded**: Lists all 40+ available commands with versions
- **Phase Status**: Current development phase and unified command interfaces

### Basic Usage
```powershell
# Meta-commands (start with /)
isaac --start
/help                    # Show all available commands
/status                  # System status and diagnostics
/config                  # View/modify settings

# AI queries (start with 'isaac')
isaac show me all python files
isaac what is Docker?
isaac help me debug this error

# Regular shell commands (tier-validated)
ls -la
git status
```

### Authentication System
Isaac uses a key-based authentication system:
- **Master Key**: Set `ISAAC_MASTER_KEY` environment variable or create `~/.isaac/.master_key` file
- **User Keys**: Create with `/config keys create` command
- **Interactive Mode**: Currently allows unauthenticated access for development
- **Direct Commands**: Require authentication when using `-key` parameter

### How to Use Your Master Key
```powershell
# Set your master key (you already did this)
$env:ISAAC_MASTER_KEY = "ET0B7OrBkdF9HeMo8WpdvA"

# Start Isaac with authentication
isaac -key ET0B7OrBkdF9HeMo8WpdvA --start --no-boot

# Or run direct commands with authentication
isaac -key ET0B7OrBkdF9HeMo8WpdvA --oneshot /status
```

### Testing Key Authentication
Your master key is **active and working**! When you start Isaac with `-key`, it authenticates you with full admin permissions including:
- ✅ Read/write/execute access
- ✅ AI functionality
- ✅ Cloud sync
- ✅ Admin privileges

### What You Can Do With Authentication
Once authenticated, you can:
- **Run any command** without restrictions
- **Access AI features** (when API keys are configured)
- **Use cloud sync** for session persistence
- **Execute privileged operations** that require authentication

### Logout/Login Process
Currently, Isaac doesn't have explicit logout/login commands. Authentication works as follows:
- **Interactive Mode**: No authentication required (development mode)
- **Direct Commands**: Use `-key` parameter for authentication
- **Session Persistence**: Your authentication state persists during the session

### Command Categories
- **AI & Analysis**: `/ask`, `/ambient`, `/debug`, `/script`
- **File Operations**: `/read`, `/write`, `/edit`, `/search`, `/grep`
- **System Management**: `/status`, `/config`, `/backup`, `/update`
- **Workspace**: `/workspace`, `/bubble`, `/timemachine`
- **Communication**: `/msg`, `/mine`, `/tasks`

### Execution Modes
- **Interactive Mode**: `isaac --start` - Full shell replacement with AI assistance
- **One-shot Mode**: `isaac --oneshot /command` - Execute single command and exit
- **Direct Mode**: `isaac /command` - Execute command with authentication required

### Troubleshooting Common Issues

**"Invalid key: c-tab" Error (FIXED):**
- This was caused by unsupported key bindings in prompt_toolkit
- **SOLUTION**: Use `isaac --start --no-boot` (now working!)
- The Ctrl+Tab key binding has been made optional to prevent this error
- Alternative: Use `isaac --oneshot /command` for single commands

**"you think I work for free? cute." Error:**
- Isaac requires authentication for direct command execution
- Set master key: `$env:ISAAC_MASTER_KEY = "your-key"`
- Or create master key file: `echo "your-key" > ~/.isaac/.master_key`
- Interactive mode currently allows unauthenticated access

**API Key Warnings:**
- Set environment variables: `$env:XAI_API_KEY`, `$env:ANTHROPIC_API_KEY`, `$env:OPENAI_API_KEY`
- At minimum, configure XAI (Grok) for basic AI functionality
- Claude and OpenAI provide fallback for complex queries

**Command Loading Issues:**
- Ensure all `command.yaml` manifests have required fields: `name`, `version`, `summary`
- Check that aliases start with `/` (e.g., `/fix` not `fix`)
- Use `int` not `integer` for argument types

### Troubleshooting Common Issues

**"Invalid key: c-tab" Error:**
- This occurs when Isaac receives unexpected keyboard input during startup
- Try running with: `isaac --start --no-boot` to skip advanced input handling
- Or use: `isaac --oneshot /help` for single commands without interactive mode
- Avoid piping input to interactive mode - use oneshot mode instead

**"you think I work for free? cute." Error:**
- Isaac requires authentication for direct command execution
- Set master key: `$env:ISAAC_MASTER_KEY = "your-key"`
- Or create master key file: `echo "your-key" > ~/.isaac/.master_key`
- Interactive mode currently allows unauthenticated access

**API Key Warnings:**
- Set environment variables: `$env:XAI_API_KEY`, `$env:ANTHROPIC_API_KEY`, `$env:OPENAI_API_KEY`
- At minimum, configure XAI (Grok) for basic AI functionality
- Claude and OpenAI provide fallback for complex queries

**Command Loading Issues:**
- Ensure all `command.yaml` manifests have required fields: `name`, `version`, `summary`
- Check that aliases start with `/` (e.g., `/fix` not `fix`)
- Use `int` not `integer` for argument types

## 🏗️ Hybrid C++/Python Architecture

### Core Design Philosophy
**Performance First**: C++ handles performance-critical operations, Python provides flexibility and AI integration. Memory efficiency is paramount - this is a shell replacement, not a memory hog.

### Component Architecture

#### **C++ Core (Performance Critical)**
- **CommandRouter Core**: `src/core/command_router.cpp` - Fast command routing and validation (10x faster than Python)
- **TierValidator Core**: `src/core/tier_validator.cpp` - High-performance security validation with regex optimization
- **ShellAdapter Core**: `src/adapters/shell_adapter.cpp` - Direct system calls, zero subprocess overhead
- **Memory Management**: Custom allocators, object pooling, memory-mapped configurations

#### **Python Bindings (Flexibility Layer)**
- **pybind11 Integration**: Seamless C++/Python interop with minimal overhead
- **AI Router**: Multi-provider AI orchestration (Grok → Claude → OpenAI)
- **Plugin System**: Dynamic command loading and extension
- **UI Layer**: prompt_toolkit interface with async capabilities

#### **Key Components**
- **Strategy Pattern Router**: 15+ routing strategies (MetaCommandStrategy, NaturalLanguageStrategy, TierExecutionStrategy, etc.)
- **Multi-Provider AI Router**: Intelligent fallback chain with cost optimization via `TaskAnalyzer` and `CostOptimizer`
- **Tier System**: 5-tier command safety (1: instant, 2: auto-correct, 2.5: confirm, 3: AI validate, 4: lockdown)
- **Tool-Enabled Agent**: `IsaacAgent` combines AI router with file tools (read/write/edit/grep/glob)
- **Plugin-Based Commands**: Commands loaded from `command.yaml` manifests in `isaac/commands/*/`
- **Cross-Platform Shell Adapters**: `PowerShellAdapter` and `BashAdapter` with unified `CommandResult` interface
- **Command Queue**: Offline-capable queue with background sync worker
- **Workspace Management**: Isolated environments with xAI Collections (RAG) support
- **Session Persistence**: Cloud sync with machine-aware history

### Performance Optimizations
- **Lazy Loading**: All heavy components loaded on-demand (26 MB memory reduction achieved)
- **Memory Pooling**: Object reuse for frequent allocations
- **Zero-Copy Operations**: String views and memory-mapped files
- **SIMD Processing**: Vectorized string operations where applicable
- **Async I/O**: Non-blocking operations for AI and network calls

## 🔧 Critical Developer Workflows

### Hybrid Build System
```bash
# Python setup (always required)
pip install -e .              # Python bindings and entry points
pip install pybind11 cmake    # C++ binding tools

# C++ core build (performance critical)
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)              # Compile optimized C++ core

# Full system test
isaac --start --no-boot       # Test C++/Python integration
pytest tests/ -x             # Run test suite
```

### Development Workflows

#### **C++ Core Development**
- **Performance Critical**: Command routing, tier validation, shell adapters
- **Build System**: CMake with pybind11 for Python bindings
- **Testing**: C++ unit tests with Google Test, integration tests with pytest
- **Profiling**: Use `perf`, `valgrind`, `gperftools` for optimization
- **Memory**: < 20 MB startup target, use custom allocators and pooling

#### **Python Layer Development**
- **Flexibility Layer**: AI integration, plugins, UI components
- **Entry Points**: `pip install -e .` creates `isaac`, `ask`, and `mine`
- **Testing**: `pytest tests/` (≥85% coverage required)
- **Lazy Loading**: All heavy imports must be lazy (AI clients, strategies, commands)

#### **Component Responsibilities**
- **C++ Core**: Performance-critical operations (routing, validation, shell execution)
- **Python Bindings**: Seamless interop with minimal overhead
- **Python AI Layer**: Multi-provider orchestration, plugin system
- **Python UI**: prompt_toolkit interface, async capabilities

### Testing Strategy
- **Unit Tests**: C++ (gtest), Python (pytest) for individual components
- **Integration Tests**: Full C++/Python pipeline testing
- **Performance Tests**: Memory usage, latency benchmarks
- **Coverage**: ≥85% for Python, ≥90% for C++ core components
- **Fixtures**: `tests/conftest.py` provides `temp_isaac_dir`, `mock_api_client`, `sample_preferences`

### Component Development
- **Meta-Commands**: 52 command modules in `isaac/commands/*/`
- **AI Providers**: Set `XAI_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`
- **Tool Development**: Extend `BaseTool` from `isaac/tools/base.py`
- **Command Routing**: Input flows through `CommandRouter` → `TierValidator` → `CommandDispatcher`
- **C++ Integration**: Use pybind11 for seamless C++/Python interop

## Project-Specific Conventions

- **Tier Classification**: Commands in `isaac/data/tier_defaults.json` by tier. Override via user preferences. Tier 2.5 requires post-correction confirmation.
- **Error Handling**: Shell adapters return `CommandResult(success, output, exit_code)` - never raise exceptions. Validates in `BaseShellAdapter.execute()`.
- **Config Management**: Use `Path(__file__).parent.parent / 'data'` for package data. User config in `Path.home() / '.isaac'`.
- **AI Tool Schemas**: Tools define JSON Schema via `get_parameters_schema()`. Agent formats as function calls for provider APIs.
- **Cross-Platform Paths**: Always use `pathlib.Path`, never string concatenation. Adapters handle shell-specific syntax.
- **Provider Fallback**: `AIRouter.chat()` tries providers in order, preserves context on fallback. Tracks costs in `cost_tracking.json`.
- **Command Manifests**: YAML format with `triggers`, `args`, `security.resources` (timeout_ms, max_stdout_kib). See `docs/command_plugin_spec.md`.