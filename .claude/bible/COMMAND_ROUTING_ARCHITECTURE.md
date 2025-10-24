# ISAAC Command Routing Architecture

## Overview
ISAAC's command router is the central nervous system that determines how user input is processed, ensuring safety, efficiency, and appropriate execution paths.

## Main Command Routing Flow

```
User Input
    │
    ├── Empty/whitespace? → Ignore
    │
    ├── Starts with "/"? → ISAAC Meta Command
    │   ├── /exit, /quit → Exit ISAAC
    │   ├── /help → Show help system
    │   ├── /status → System status
    │   ├── /config → Configuration management
    │   ├── /mine → Mining/collection system
    │   ├── /ask, /a → AI chat (streaming eligible)
    │   └── Other → Plugin command dispatch
    │
    └── No "/" prefix → Potential Shell Command
        │
        ├── Contains "|" (pipe)? → Pipeline Processing
        │   ├── Parse pipeline segments
        │   ├── Execute each segment
        │   ├── Pass data between stages
        │   └── Return final result
        │
        └── Single command → Direct Execution
            │
            ├── Tier Classification (1-4)
            │   ├── Tier 1: Instant (ls, cd, pwd)
            │   ├── Tier 2: Auto-correct (grep, head)
            │   ├── Tier 3: AI validation (cp, mv, git)
            │   └── Tier 4: Explicit confirm (rm, dd)
            │
            ├── Apply Safety Rules
            │   ├── Command validation
            │   ├── Path safety checks
            │   └── Resource limits
            │
            └── Execute Command
                │
                ├── Shell Adapter (PowerShell/Bash)
                │   ├── Command translation
                │   ├── Execution environment
                │   └── Result capture
                │
                └── Return Result
                    ├── Success: Output display
                    ├── Error: Error handling
                    └── Logging: Session history
```

## Safety-First Design

### Tier System Integration
```
Command → Classification → Safety Validation → Execution
    ↓         ↓              ↓              ↓
  Input    Tiers 1-4    AI Validation    Shell/Plugin
                    (Tier 3+ only)
```

### Pipeline Safety
```
cmd1 | cmd2 | cmd3
    ↓     ↓     ↓
  Validate  Validate  Validate
    ↓     ↓     ↓
  Execute  Execute  Execute
    ↓     ↓     ↓
  Data →  Data →  Data → Final Result
  Flow   Flow   Flow
```

## Key Architectural Principles

1. **Explicit AI Intent**: `/ask` and `/a` clearly signal AI interaction
2. **Tiered Safety**: Progressive validation based on command risk
3. **Pipeline Support**: Data flow between commands with safety checks
4. **Plugin Architecture**: Extensible command system via manifests
5. **Session Awareness**: All commands logged and tracked

## Error Handling Flow

```
Command Execution
    │
    ├── Success → Display result + Log to session
    │
    └── Failure → Error classification
        │
        ├── Network/API error → Retry logic
        ├── Permission error → User feedback
        ├── Command not found → Suggestion system
        ├── Timeout → Cancellation options
        └── Unknown error → Safe failure + logging
```

## Performance Considerations

- **Lazy Loading**: Commands loaded on first use
- **Caching**: Frequent command results cached
- **Async Support**: Long-running commands can be backgrounded
- **Resource Limits**: Memory/CPU/time bounds enforced

*Documented: October 23, 2025*