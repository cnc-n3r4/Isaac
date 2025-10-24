# ISAAC Mining System Architecture

## Overview
The mining system provides a metaphorical interface for xAI collections management, using mining terminology to make complex operations intuitive. The design supports arrays at different hierarchical levels: collection arrays for grouping xAI collections, sub-group arrays within individual collections, and cross-collection file arrays for organizing files regardless of their source collection.

## Mining Workflow Flow

```
User Command (/mine)
    │
    ├── Collection Array Management
    │   ├── --drift <name> → Create array of xAI collections
    │   └── --claim <array> → Switch to collection array
    │
    ├── Ore Processing
    │   ├── --muck <file> → Upload file to active collection
    │   └── --muck <file> --to-drift <name> → Upload file to specific sub-group
    │
    ├── File Array Management
    │   └── --skip <name> → Create array of files (cross-collection)
    │
    ├── Exploration & Search
    │   ├── --survey <query> → Search all collections, show top collections + file teases
    │   ├── --survey <query> --to-map <name> → Survey with sub-group focus
    │   ├── --dig <query> → Search active collection, show files + snippets
    │   └── --dig <query> --to-drift <name> → Search specific sub-group array
    │
    └── File Operations
        ├── --haul <file> → Attach file for detailed querying
        ├── --haul <file> --to-skip <name> → Attach file + file array focus
        ├── --pan <query> → Query the attached file for details
        └── --drop <file> → Delete the file
```

## Mining Metaphor Mapping

```
Real Concept → Mining Term → Command
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Collection    → Claim       → --stake/--claim
Sub-group     → Drift       → --to-drift
Coll Array    → Drift       → --drift
File Array    → Skip        → --skip
Upload file   → Muck        → --muck
Create coll   → Stake       → --stake
Switch coll   → Claim       → --claim
Search all    → Survey      → --survey
Search active → Dig         → --dig
Attach file   → Haul        → --haul
Query file    → Pan         → --pan
Delete coll   → Abandon     → --abandon
Delete file   → Drop        → --drop
```

## Data Flow Architecture

```
Hierarchical Array Structure
    │
    ├── Collection Arrays (--drift)
    │   └── Groups of xAI collections
    │       └── Cross-collection organization
    │
    └── Collections
        │
        ├── Sub-group Arrays (within collections)
        │   └── Organized sections within individual collections
        │
        └── Files
            │
            └── File Arrays (--skip)
                └── Groups of files across different collections
                    └── Cross-collection file organization
```

```
Upload Flow
    │
    ├── Muck (--muck <file>)
    │   └── Upload file to xAI collection
    │       ├── Process file content
    │       ├── Generate embeddings
    │       ├── Add to collection search index
    │       └── Return file reference
```

```
User Query Flow
    │
    ├── Survey (--survey <query>)
    │   └── Cross-collection search
    │       ├── Find relevant collections
    │       ├── Show collection previews
    │       └── File content teases
    │
    └── Focused Analysis
        ├── Claim (--claim) → Set active collection
        ├── Dig (--dig) → Search within collection
        ├── Haul (--haul) → Attach specific file
        └── Pan (--pan) → Query attached file details
            │
            └── File Content Analysis
                ├── Semantic search within file
                ├── Code analysis (if applicable)
                ├── Context extraction
                └── Detailed responses
```

## Session Integration

```
Mining Operations ↔ Session Manager
    │
    ├── Active collection tracking
    │   ├── Current collection ID
    │   ├── Current collection name
    │   └── Current sub-group array (drift)
    │
    ├── Array management
    │   ├── Collection arrays (groups of xAI collections)
    │   ├── Sub-group arrays (within individual collections)
    │   ├── File arrays (cross-collection file groups)
    │   └── Array creation/modification
    │
    ├── Attached file state
    │   ├── Currently hauled file ID
    │   ├── File metadata cache
    │   └── Query context
    │
    └── History logging
        ├── All mining operations
        ├── Search queries and results
        ├── Array operations at all levels
        ├── File uploads and processing
        ├── File attachments and queries
        └── Collection switches
```

## Error Handling & Recovery

```
Mining Operation
    │
    ├── API Connection
    │   ├── xAI service available? → Continue
    │   └── No connection → Graceful failure
    │
    ├── Collection Access
    │   ├── Valid collection ID? → Continue
    │   └── Invalid/missing → Clear active + error
    │
    ├── File Operations
    │   ├── File exists? → Continue
    │   ├── Valid file_id? → Continue
    │   └── Invalid → Nugget search suggestions
    │
    └── Recovery Options
        ├── Auto-fix (clear invalid state)
        ├── Retry (transient failures)
        ├── Skip (continue with next)
        ├── Abort (stop operation)
        └── Suggest (alternative commands)
```

## Performance Optimizations

- **Lazy Loading**: Collections loaded on demand
- **Caching**: Recent searches cached locally
- **Batch Operations**: Multiple files can be processed together
- **Progress Tracking**: Large uploads show progress
- **Background Processing**: Long operations can be queued

## Future Extensions


*Documented: October 23, 2025*