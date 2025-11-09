# ISAAC Plugin System - Quick Reference

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────┐
│ Isaac Application                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  PluginManager                                            │
│  ├── Discovery: ~/.isaac/plugins/installed.json          │
│  ├── Loading: Dynamic module import                       │
│  ├── Lifecycle: install/enable/disable/uninstall        │
│  └── Hook System: 15+ event hooks                         │
│                                                            │
│  Hook Triggers:                                           │
│  ├── STARTUP              (app startup)                   │
│  ├── BEFORE_COMMAND       (command execution)            │
│  ├── FILE_CHANGED         (file system events)           │
│  ├── BEFORE_AI_QUERY      (AI integration)               │
│  └── ... (12 more hooks)                                  │
│                                                            │
│  Security Layer:                                          │
│  ├── PluginSandbox (resource limits, timeouts)          │
│  ├── Import Guard (block dangerous modules)              │
│  ├── File Guard (path whitelisting)                      │
│  └── SecurityPolicy (configurable constraints)           │
│                                                            │
└────────────────────────────────────────────────────────────┘
         │                          │
         ▼                          ▼
┌────────────────────┐  ┌───────────────────────┐
│ Plugin Instance    │  │ Plugin Registry       │
│                    │  │                       │
│ MyPlugin(Plugin)   │  │ - Discovery           │
│ ├── metadata       │  │ - Search              │
│ ├── initialize()   │  │ - Download            │
│ ├── shutdown()     │  │ - Caching (1h TTL)    │
│ └── handlers       │  │ - Verification       │
│                    │  │                       │
└────────────────────┘  └───────────────────────┘
```

## Plugin Structure

```
my-plugin/
├── plugin.py              REQUIRED - Main plugin code
│   class MyPlugin(Plugin):
│       @property metadata
│       def initialize()
│       def shutdown()
│       def on_hook_name()
│
├── manifest.json          REQUIRED - Metadata
│   {
│     "name": "my-plugin",
│     "version": "1.0.0",
│     "author": "...",
│     "description": "...",
│     "hooks": [...],
│     "permissions": [...]
│   }
│
├── README.md              REQUIRED - Documentation
├── test_plugin.py         Generated - Unit tests
└── __init__.py            Generated - Package marker
```

## Key Classes & Interfaces

### Plugin (Abstract Base Class)
```python
class Plugin(ABC):
    @property
    def metadata(self) -> PluginMetadata:        # REQUIRED
        ...
    
    def initialize(self, context: PluginContext) -> None:  # REQUIRED
        ...
    
    def shutdown(self) -> None:                   # Optional
        ...
    
    # Hook management
    def register_hook(hook, handler)
    def get_hooks(hook) -> List[Callable]
    def get_all_hooks() -> Set[PluginHook]
    
    # State management
    def get_state(key, default=None)
    def set_state(key, value)
    def get_config(key, default=None)
```

### PluginContext
```python
@dataclass
class PluginContext:
    session_id: str
    workspace_path: str
    config: Dict[str, Any]           # permissions, plugin_name
    state: Dict[str, Any]             # plugin state storage
    event_data: Dict[str, Any]        # hook event data
    apis: Dict[str, Any]              # available APIs
```

### Available Hooks
```
Lifecycle:      STARTUP, SHUTDOWN
Commands:       BEFORE_COMMAND, AFTER_COMMAND, COMMAND_ERROR
Files:          FILE_CHANGED, FILE_CREATED, FILE_DELETED
AI:             BEFORE_AI_QUERY, AFTER_AI_RESPONSE
Workflow:       DEBUG_START, DEBUG_COMPLETE, PIPELINE_START, 
                PIPELINE_COMPLETE, MEMORY_SAVE, MEMORY_LOAD
Custom:         CUSTOM
```

## Plugin Development Workflow

### 1. Create Plugin from Template
```bash
isaac plugin create my-plugin
# Interactive prompts for:
# - Author name
# - Description
# - Hooks to use
```

### 2. Implement Plugin Logic
```python
# Edit my-plugin/plugin.py
class MyPlugin(Plugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            author="Your Name",
            description="My custom plugin",
            hooks=[PluginHook.STARTUP],
            permissions=[]  # "file:read", "subprocess", etc.
        )
    
    def initialize(self, context: PluginContext) -> None:
        self._context = context
        self.register_hook(PluginHook.STARTUP, self.on_startup)
    
    def on_startup(self) -> None:
        print("Plugin is running!")
```

### 3. Validate & Test
```bash
isaac plugin validate ./my-plugin       # Check structure
isaac plugin test ./my-plugin           # Run unit tests
```

### 4. Package & Install
```bash
isaac plugin package ./my-plugin        # Create .tar.gz
isaac plugin install my-plugin          # Install locally
isaac plugin enable my-plugin           # Enable if disabled
```

## Security Model

### Sandboxing (Enabled by Default)
```python
manager = PluginManager(enable_sandbox=True)  # Default
```

### Resource Limits
```
Memory:        100 MB (configurable)
CPU Time:      5 seconds (configurable)
File Size:     10 MB (configurable)
```

### Blocked Operations
```
Default Blocked:
- Network (socket, http, urllib, requests)
- Subprocess execution
- File writes (unless permission granted)
- Dangerous modules (os.system, eval, exec, compile)
```

### Permissions System
```python
# Declare in plugin metadata
"permissions": ["file:read", "file:write", "subprocess", "network"]

# Check at runtime
if context.has_permission("file:write"):
    # Can write files
```

## Common Patterns

### Pattern 1: Simple Hook Handler
```python
def initialize(self, context: PluginContext) -> None:
    self._context = context
    self.register_hook(PluginHook.STARTUP, self.on_startup)

def on_startup(self) -> None:
    print("Hello from plugin!")
```

### Pattern 2: Using Event Data
```python
def on_before_command(self) -> None:
    command = self._context.event_data.get("command", "")
    print(f"About to run: {command}")
```

### Pattern 3: Persistent State
```python
def on_after_command(self) -> None:
    count = self.get_state("command_count", 0) + 1
    self.set_state("command_count", count)
    print(f"Total commands: {count}")
```

### Pattern 4: File Operations (with permissions)
```python
@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="logger",
        # ...
        permissions=["file:write"]
    )

def on_startup(self) -> None:
    with open("/path/to/log.txt", "a") as f:
        f.write("Started\n")
```

### Pattern 5: External Command (with permissions)
```python
import subprocess

@property
def metadata(self) -> PluginMetadata:
    return PluginMetadata(
        name="git-plugin",
        # ...
        permissions=["subprocess"]
    )

def get_git_status(self) -> str:
    result = subprocess.run(
        ["git", "status"],
        capture_output=True,
        text=True
    )
    return result.stdout
```

## CLI Commands

### User Commands
```bash
isaac plugin install <name>              # Install plugin
isaac plugin uninstall <name>            # Uninstall plugin
isaac plugin enable <name>               # Enable plugin
isaac plugin disable <name>              # Disable plugin
isaac plugin list                        # List installed
isaac plugin search <query>              # Search registry
isaac plugin info <name>                 # Plugin details
isaac plugin update <name>               # Update plugin
isaac plugin update --all                # Update all
isaac plugin featured                    # Show featured plugins
```

### Developer Commands
```bash
isaac plugin create <name>               # Create new plugin
isaac plugin validate <path>             # Validate structure
isaac plugin test <path>                 # Run tests
isaac plugin package <path>              # Package for distribution
```

## Plugin Lifecycle

```
Create (plugin create)
    ↓
Implement (edit plugin.py)
    ↓
Validate (plugin validate)
    ↓
Test (plugin test)
    ↓
Install (plugin install)
    ↓
Initialize (plugin.initialize() called automatically)
    ↓
Running (hooks triggered on events)
    ↓
Disable (plugin disable)
    ↓
Uninstall (plugin uninstall)
```

## File System

```
~/.isaac/
├── plugins/
│   ├── installed.json              # Metadata registry
│   ├── plugin-name-1/
│   │   ├── plugin.py
│   │   ├── manifest.json
│   │   └── README.md
│   └── plugin-name-2/
│       └── ...
└── plugin_cache/
    └── registry.json               # Downloaded registry (1h cache)
```

## Troubleshooting

### Plugin won't load
1. Check `/home/user/Isaac/isaac/plugins/examples/` for pattern
2. Verify plugin.py has valid Plugin subclass
3. Check manifest.json is valid JSON
4. Review sandbox permissions

### Permission denied errors
1. Add required permission to metadata: `"permissions": ["file:write"]`
2. Check allowed paths are configured in SecurityPolicy
3. Disable sandbox for debugging: `PluginManager(enable_sandbox=False)`

### Plugin crashes
1. Check sandbox timeout (default 5 seconds)
2. Check memory limit (default 100 MB)
3. Review logs in ~/.isaac/plugins/
4. Add error handling to hook handlers

### Missing hooks
1. Verify hook name matches PluginHook enum
2. Check hook is registered: `self.register_hook(PluginHook.STARTUP, self.on_startup)`
3. Ensure hook name exists in PluginHook enum

## Examples

Three example plugins are included:

1. **hello_world.py** - Simplest example
   - Basic hooks (STARTUP, BEFORE_COMMAND)
   - ~50 lines, good starting point

2. **git_status.py** - Real-world example
   - File system access, subprocess
   - Shows permission usage
   - Git integration

3. **command_logger.py** - Advanced example
   - State management
   - Multiple hooks (4)
   - Persistent JSON logging
   - Shows all patterns

## Integration Points

### How Isaac Calls Plugins
```python
from isaac.plugins import PluginManager, PluginHook

manager = PluginManager()

# On startup
manager.trigger_hook(PluginHook.STARTUP)

# Before command
manager.trigger_hook(PluginHook.BEFORE_COMMAND, 
                     event_data={"command": "test"})

# After command
manager.trigger_hook(PluginHook.AFTER_COMMAND,
                     event_data={"result": "success"})

# On shutdown
for plugin in manager.list_enabled():
    plugin.shutdown()
```

## Performance Considerations

1. **Hooks are executed synchronously** - Keep handlers fast
2. **CPU timeout: 5 seconds** - Long operations need optimization
3. **Memory limit: 100 MB** - Avoid large data structures
4. **All plugins in same process** - One crash affects all

## Best Practices

1. Keep hook handlers fast (< 100ms)
2. Use state management for persistence
3. Handle errors gracefully
4. Request only needed permissions
5. Clean up resources in shutdown()
6. Document your plugin in README.md
7. Write unit tests
8. Use meaningful plugin/version names (semantic versioning)
9. Test with sandbox enabled
10. Don't assume absolute paths - use context.workspace_path

