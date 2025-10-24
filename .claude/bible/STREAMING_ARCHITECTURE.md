# ISAAC Streaming Decision Tree

## Overview
ISAAC uses explicit command prefixes to determine when streaming AI responses is safe vs when synchronous processing is required.

## Streaming Decision Flow

```
User Input
    │
    ├── Is command /ask or /a?
    │   ├── YES (explicit AI intent) → Safe to stream
    │   │   ├── Contains pipe (|) → SYNC MODE
    │   │   │   └── Reason: Data processing pipeline
    │   │   └── No pipe → ASYNC/STREAMING MODE
    │   │       └── Reason: Pure AI chat conversation
    │   │
    │   └── NO (might be shell command) → SYNC MODE
    │       └── Reason: Safety - could be shell command
    │
    └── Examples:
        ├── isaac /ask "weather?" → STREAM ✓
        ├── isaac /a "explain CNC" → STREAM ✓
        ├── isaac /ask "analyze" | save → SYNC ✗
        └── isaac ls -la → SYNC ✗
```

## Implementation Rules

### Stream-Safe Commands
- **Prefix**: `/ask` or `/a`
- **Context**: No pipes, pure AI interaction
- **Behavior**: Progressive response display
- **Interruption**: User can cancel mid-stream

### Sync-Only Commands
- **No AI prefix**: Potential shell commands
- **With pipes**: Data processing workflows
- **Behavior**: Complete response before display
- **Safety**: Prevents streaming shell output

## Benefits

1. **Architectural Safety**: Only streams when intent is explicit
2. **User Control**: Clear distinction between chat and commands
3. **Pipeline Compatibility**: Piping works with sync processing
4. **Backwards Compatible**: Existing shell commands unchanged

## Future Extensions
```
Streaming Candidates:
├── /chat → Dedicated chat interface
├── /think → Long-form reasoning
└── /code → Code generation with streaming
```

*Documented: October 23, 2025*