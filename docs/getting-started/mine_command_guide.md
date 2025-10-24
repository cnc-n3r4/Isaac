# Isaac /mine Command - Personal Collection Search Guide

## Overview

The `/mine` command is Isaac's personal knowledge search system. Unlike internet searches, `/mine` searches through **your own files and documents** that you've uploaded to personal collections. This includes project files, notes, logs, and any documents you want to make searchable.

Think of it as having your own personal Google, but for your files only.

## Quick Start for Beginners

### Step 1: First Time Setup
```bash
# Start Isaac
isaac /start

# Check if collections are enabled
isaac /config --status
```

### Step 2: Create Your First Collection
```bash
# Create a collection for your project files
isaac /mine --stake myproject

# Upload some files to search
isaac /mine --muck README.md
isaac /mine --muck notes.txt
isaac /mine --muck *.py
```

### Step 3: Search Your Files
```bash
# Ask questions about your files
isaac /mine --dig "what is this project about?"
isaac /mine --dig "find the function that handles user login"
isaac /mine --dig "show me all error handling code"
```

## Understanding Collections

### What Are Collections?
Collections are like folders for your searchable files. Each collection:
- Has a unique name and ID
- Contains uploaded files and documents
- Can be searched independently
- Is stored securely in the cloud

### Collection Types
- **Personal Collections**: Your private files (default)
- **Project Collections**: Group files by project
- **Archive Collections**: Old files you still want to search
- **Reference Collections**: Documentation, manuals, etc.

## Basic Commands

### Creating Collections
```bash
# Create a new collection (stake your claim)
isaac /mine --stake mydocs

# Create a collection group/folder (drift system)
isaac /mine --drift project-docs

# List all your collections
isaac /mine --maps
```

**What's the difference?**
- `--stake`: Creates individual collections for organizing your files
- `--drift`: Creates groups/arrays of related collections (advanced feature)

### Uploading Files (Mucking)
```bash
# Upload a single file
isaac /mine --muck important-document.pdf

# Upload multiple files with wildcards
isaac /mine --muck *.txt
isaac /mine --muck src/**/*.py

# Upload from a specific directory
isaac /mine --muck /path/to/my/files/*.md
```

### Searching (Digging)
```bash
# Basic search
isaac /mine --dig "what is machine learning?"

# Search with context
isaac /mine --dig "find the bug in the login function"

# Search specific file types
isaac /mine --dig "error handling" --type python

# Search within date range
isaac /mine --dig "project updates" --since "2024-01-01"
```

## Advanced Features

### Search Settings Configuration
```bash
# Open the configuration console
isaac /config console

# Navigate to Collections tab and adjust:
# - max_chunk_size: How much text to process per file chunk
# - match_preview_length: How much context to show in results
# - multi_match_count: How many matches to return
# - show_scores: Display relevance scores
```

### File-Specific Search
```bash
# Attach specific files for detailed querying
isaac /mine --haul file1.txt file2.py
isaac /mine --pan "search term"

# Create file array for cross-collection focus
isaac /mine --skip myfiles --haul file1.txt file2.py
isaac /mine --pan "search term" --to-skip myfiles

# Remove attached files
isaac /mine --drop file1.txt
```

### Search Results and Piping
```bash
# Get detailed results
isaac /mine --dig "my question" --verbose

# Pipe results to other commands
isaac /mine --dig "error messages" | grep "Exception"

# Save results to file
isaac /mine --dig "important info" > results.txt
```

## Configuration Options

### Search Parameters
| Setting | Default | Description |
|---------|---------|-------------|
| max_chunk_size | 1000 | Characters per text chunk |
| match_preview_length | 200 | Characters of context in results |
| multi_match_count | 5 | Number of matches to return |
| piping_threshold | 0.7 | Minimum relevance for piping |
| show_scores | true | Show relevance scores |

### File Restrictions
```bash
# Limit search to specific files only
isaac /config console
# Collections tab → "Search only specific files" → Add file IDs
```

## Troubleshooting

### Common Issues

**"No collections found"**
```bash
# Create your first collection
isaac /mine --stake myfirstcollection

# Check if collections are enabled in config
isaac /config --status
```

**"Search returned no results"**
```bash
# Make sure files are uploaded
isaac /mine --maps  # List all collections

# Try different search terms
isaac /mine --dig "keyword1 keyword2"

# Check file types are supported
isaac /mine --muck file.pdf  # PDFs are supported
```

**"API key not configured"**
```bash
# Configure xAI API keys
isaac /config --set xai.collections.api_key YOUR_API_KEY
isaac /config --set xai.collections.management_api_key YOUR_MANAGEMENT_KEY
```

### Getting Help
```bash
# Show all mine commands
isaac /mine --help

# Check system status
isaac /status

# View configuration
isaac /config --status
```

## Best Practices

### Organization
1. **Use descriptive collection names**: `project-alpha`, `personal-notes`, `research-papers`
2. **Group related files**: Keep project files in project collections
3. **Regular uploads**: Upload new files as you create them
4. **Archive old collections**: Move completed projects to archive collections

### Search Tips
1. **Be specific**: "login function bug" is better than "bug"
2. **Use keywords**: Include technical terms, function names, class names
3. **Try variations**: If one search doesn't work, try synonyms
4. **Use quotes**: For exact phrases: `"exact phrase here"`

### Performance
1. **Chunk size**: Larger chunks (2000+) for better context, smaller (500) for speed
2. **File limits**: Use file restrictions for large codebases
3. **Regular cleanup**: Delete unused collections to save space

## Examples by Use Case

### Software Development
```bash
# Create project collection
isaac /mine --stake myapp

# Upload codebase
isaac /mine --muck src/**/*.py
isaac /mine --muck docs/**/*.md

# Search for specific functionality
isaac /mine --dig "user authentication logic"
isaac /mine --dig "database connection code"
isaac /mine --dig "error handling patterns"
```

### Research and Writing
```bash
# Create research collection
isaac /mine --stake research

# Upload papers and notes
isaac /mine --muck papers/*.pdf
isaac /mine --muck notes/*.txt

# Find information
isaac /mine --dig "machine learning algorithms"
isaac /mine --dig "experimental results"
```

### Personal Knowledge Base
```bash
# Create personal collection
isaac /mine --stake personal

# Upload various documents
isaac /mine --muck recipes/*.txt
isaac /mine --muck manuals/*.pdf
isaac /mine --muck notes/*.md

# Search your knowledge
isaac /mine --dig "chocolate cake recipe"
isaac /mine --dig "computer repair guide"
```

## Integration with Other Features

### With Task Mode
```bash
# Use search results in tasks
isaac task: analyze the login function and fix any bugs
# Isaac will search your collections for relevant code
```

### With Piping
```bash
# Combine searches with other commands
isaac /mine --dig "error logs" | grep "CRITICAL"
isaac /mine --dig "user functions" | wc -l
```

### With Workspaces
```bash
# Switch to project workspace
isaac workspace switch myproject

# Search within that workspace's files
isaac /mine --dig "project requirements"
```

## Security and Privacy

- **Your files only**: `/mine` searches only files you've uploaded
- **Cloud storage**: Files are stored securely in xAI's cloud
- **Access control**: Only you can access your collections
- **No internet searches**: Results come from your personal files only

## Getting Started Checklist

- [ ] Start Isaac: `isaac /start`
- [ ] Check configuration: `isaac /config --status`
- [ ] Create first collection: `isaac /mine --stake mycollection`
- [ ] Upload some files: `isaac /mine --muck file1.txt file2.md`
- [ ] Try a search: `isaac /mine --dig "what's in these files?"`
- [ ] Explore settings: `isaac /config console`

Remember: `/mine` is about searching **your** knowledge, not the internet's. Upload your files, ask questions, get answers from your own content!</content>
<parameter name="filePath">c:\Projects\Isaac-1\instructions\mine_command_guide.md