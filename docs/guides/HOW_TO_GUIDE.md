# Isaac 2.0 - How-To Guide

Practical guides for common tasks and workflows with Isaac.

---

## Table of Contents

1. [Workspace Management](#workspace-management)
2. [AI Features](#ai-features)
3. [File Operations](#file-operations)
4. [Unix Aliases on Windows](#unix-aliases-on-windows)
5. [Command Piping](#command-piping)
6. [xAI Collections (RAG)](#xai-collections-rag)
7. [Configuration Management](#configuration-management)
8. [Backup & Restore](#backup--restore)
9. [Advanced Workflows](#advanced-workflows)

---

## Workspace Management

### Creating Workspaces

Workspaces provide isolated environments for different projects.

#### Basic Workspace

```bash
# Create simple workspace
/workspace create myproject

# Creates: ~/.isaac/workspaces/myproject/
```

#### Workspace with Virtual Environment

```bash
# Create workspace with Python venv
/workspace create myproject --venv

# Activate the virtual environment (Windows)
cd ~/.isaac/workspaces/myproject
activate_venv.bat

# Activate the virtual environment (Linux/macOS)
source ~/.isaac/workspaces/myproject/.venv/bin/activate
```

#### Workspace with xAI Collection

```bash
# Create workspace with RAG collection
/workspace create myproject --collection

# Creates xAI collection named "workspace-myproject"
# You can upload docs for context-aware AI assistance
```

#### Full-Featured Workspace

```bash
# Create workspace with everything
/workspace create myproject --venv --collection

# You get:
# ✓ Isolated directory
# ✓ Python virtual environment
# ✓ xAI collection for RAG
# ✓ Metadata tracking
```

### Managing Workspaces

```bash
# List all workspaces
/workspace list

# Switch to workspace (changes directory)
/workspace switch myproject

# Delete workspace
/workspace delete myproject

# Delete workspace but keep xAI collection
/workspace delete myproject --preserve-collection
```

### Workspace Workflow Example

```bash
# 1. Create workspace for new project
/workspace create web-scraper --venv --collection

# 2. Switch to workspace
/workspace switch web-scraper

# 3. Install dependencies
pip install requests beautifulsoup4

# 4. Upload documentation to collection
/mine upload workspace-web-scraper docs/*.md

# 5. Work with AI context
/ask how do I scrape dynamic JavaScript content?
# AI has access to your uploaded docs via RAG

# 6. Create files
/newfile scraper.py

# 7. When done, switch to another workspace
/workspace switch other-project
```

---

## AI Features

### Asking Questions (/ask)

The `/ask` command provides conversational AI without executing commands.

```bash
# General knowledge
/ask what is Kubernetes?

# Technical questions
/ask explain Docker containers vs virtual machines

# Programming help
/ask how do I use async/await in Python?

# Best practices
/ask what are best practices for REST API design?
```

**When to use `/ask` vs natural language:**
- Use `/ask` for questions and explanations
- Use `isaac <query>` for command execution

### Natural Language Commands

Natural language commands must start with "isaac" and result in command execution.

```bash
# Find files
isaac show me all python files
# Translates to: find . -name "*.py"

isaac find files larger than 100MB
# Translates to: find . -type f -size +100M

# Git operations
isaac show me git commits from last week
# Translates to: git log --since="1 week ago"

# File operations
isaac count lines in all JavaScript files
# Translates to: find . -name "*.js" -exec wc -l {} +
```

**Important**: The AI distinguishes between:
- Geographic questions: "where is Alaska?" → Information
- File questions: "where is alaska.exe?" → Suggests command

### Task Mode

Break down complex tasks into steps.

```bash
isaac task: set up a new Python project with pytest and black

# Isaac will:
# 1. Create project structure
# 2. Initialize git repository
# 3. Create virtual environment
# 4. Install pytest and black
# 5. Configure pyproject.toml
# 6. Create initial test file
```

### Code Analysis

```bash
# Analyze a file
/analyze path/to/code.py

# AI provides:
# - Code quality assessment
# - Potential bugs
# - Performance suggestions
# - Security issues
# - Best practices violations
```

### AI Provider Management

```bash
# Check AI status
/config ai

# Shows:
# - Active providers
# - API key status
# - Cost tracking
# - Usage statistics

# Switch preferred provider
/config set ai.routing.prefer_provider claude

# Disable a provider
/config set ai.providers.grok.enabled false
```

---

## File Operations

### Reading Files

```bash
# Read entire file
/read README.md

# Read specific line range
/read file.txt --lines 10-20

# Read with line numbers
/read script.py
# Output shows line numbers: 1→ #!/usr/bin/env python
```

### Writing Files

```bash
# Write new file
/write output.txt "Hello World"

# Write with multiline content
/write config.yaml "
name: myapp
version: 1.0
"

# Write from command output
/write output.txt "$(ls -la)"
```

### Editing Files

```bash
# Replace exact string
/edit file.txt "old text" "new text"

# Replace all occurrences
/edit file.txt "old" "new" --all

# Case-sensitive replacement
/edit file.txt "OldText" "NewText"
```

### Creating Files with Templates

```bash
# Create Python file with starter template
/newfile app.py
# Creates file with:
# #!/usr/bin/env python
# if __name__=='__main__':
#     print('hello')

# Create with custom content
/newfile notes.txt --content "Project notes"

# Create from specific template
/newfile index.html --template .html

# List available templates
/newfile --list-templates

# Add custom template
/newfile --set-template .go "package main\n\nfunc main() {\n}\n"

# Force overwrite existing file
/newfile existing.txt --force
```

### Searching Code

```bash
# Search for pattern in files
/grep "TODO" **/*.py

# Case-insensitive search
/grep -i "error" *.log

# Show context (3 lines before/after)
/grep -C 3 "function" app.js

# Search with line numbers
/grep -n "import" src/*.py

# Count matches
/grep --count "TODO" *.py
```

### Finding Files

```bash
# Find files by pattern
/glob "**/*.py"

# Find specific extension
/glob "*.md"

# Find in subdirectories
/glob "src/**/*.js"

# Find test files
/glob "**/*test*.py"
```

### File Operation Workflow

```bash
# 1. Find files matching pattern
/glob "**/*.py" | /save python_files.txt

# 2. Search for TODOs
/grep "TODO" **/*.py | /save todos.txt

# 3. Read TODO list
/read todos.txt

# 4. Analyze code quality
/analyze src/main.py

# 5. Create new module
/newfile src/utils.py

# 6. Edit configuration
/edit config.json "debug: false" "debug: true"
```

---

## Unix Aliases on Windows

### Enabling Unix Aliases

```bash
# Enable automatic translation
/alias --enable

# Now Unix commands work in PowerShell:
ls -la          # → Get-ChildItem -Force | Format-List
grep "text" *   # → Select-String "text" *
cat file.txt    # → Get-Content file.txt
```

### Available Unix Aliases

```bash
# View all aliases
/alias

# Get details on specific command
/alias --show ls

# Shows:
# ls: List directory
# Examples:
#   Unix:       ls -la
#   PowerShell: Get-ChildItem -Force | Format-List
```

### Supported Commands

| Unix Command | PowerShell Equivalent |
|--------------|----------------------|
| `ls` | `Get-ChildItem` |
| `cd` | `Set-Location` |
| `pwd` | `Get-Location` |
| `cat` | `Get-Content` |
| `grep` | `Select-String` |
| `find` | `Get-ChildItem -Recurse` |
| `rm` | `Remove-Item` |
| `cp` | `Copy-Item` |
| `mv` | `Move-Item` |
| `mkdir` | `New-Item -ItemType Directory` |
| `touch` | `New-Item -ItemType File` |
| `ps` | `Get-Process` |
| `kill` | `Stop-Process` |
| `which` | `Get-Command` |
| `head` | `Get-Content \| Select-Object -First` |
| `tail` | `Get-Content \| Select-Object -Last` |
| `wc` | `Measure-Object` |

### Custom Aliases

```bash
# Add custom alias
/alias --add ll "ls -la"

# Now you can use:
ll
# Executes: ls -la

# Remove custom alias
/alias --remove ll

# Disable automatic translation
/alias --disable
```

### Cross-Platform Development

```bash
# Developer on Windows wants to use Unix commands
/alias --enable

# Write scripts using Unix commands
/newfile build.sh
# Content:
#!/bin/bash
find . -name "*.pyc" -delete
grep -r "TODO" src/
ls -la dist/

# Commands work transparently on Windows via translation
```

---

## Command Piping

### Basic Piping

```bash
# Read file, search pattern, save results
/read app.log | /grep "ERROR" | /save errors.txt

# Find files and count them
/glob "**/*.py" | /write python_count.txt

# Chain multiple operations
/read data.csv | /grep "2024" | /save 2024_data.csv
```

### Advanced Piping

```bash
# Analyze code and save report
/analyze src/main.py | /save analysis_report.txt

# Search and summarize
/grep "TODO" **/*.py | /summarize | /save todo_summary.txt

# Create file from search results
echo "Found files:" | /newfile results.txt
/glob "**/*.md" | /newfile -f results.txt
```

### Piping with Regular Commands

```bash
# Mix Isaac commands with shell commands
ls | /grep ".py" | /save python_files.txt

# Process output
cat data.txt | /grep "pattern" | /write filtered.txt
```

---

## xAI Collections (RAG)

xAI Collections enable Retrieval-Augmented Generation (RAG) for context-aware AI.

### Creating Collections

```bash
# Create collection
/mine create project_docs

# Create collection with specific settings
/mine create codebase --description "Main codebase documentation"
```

### Uploading Documents

```bash
# Upload single file
/mine upload project_docs README.md

# Upload multiple files
/mine upload project_docs *.md

# Upload entire directory
/mine upload project_docs docs/
```

### Searching Collections

```bash
# Search for information
/mine search project_docs "how to authenticate users"

# Returns relevant context from uploaded documents
```

### Managing Collections

```bash
# List all collections
/mine list

# Get collection details
/mine info project_docs

# Delete collection
/mine delete project_docs

# Claim existing collection
/mine claim workspace-myproject
```

### RAG Workflow Example

```bash
# 1. Create workspace with collection
/workspace create api-project --collection

# 2. Upload documentation
/mine upload workspace-api-project docs/*.md
/mine upload workspace-api-project README.md
/mine upload workspace-api-project ARCHITECTURE.md

# 3. Upload code for reference
/mine upload workspace-api-project src/**/*.py

# 4. Ask context-aware questions
/mine search workspace-api-project "explain the authentication flow"
# Returns: References to auth.py, docs/auth.md with relevant snippets

# 5. Use in development
/ask how should I implement OAuth2?
# AI has access to your project documentation via RAG
```

---

## Configuration Management

### Viewing Configuration

```bash
# View all configuration
/config

# View specific section
/config ai
/config cloud
/config plugins
/config collections
```

### Modifying Configuration

```bash
# Set single value
/config set default_tier 2

# Set nested value
/config set ai.routing.prefer_provider claude

# Enable/disable features
/config set workspace.enabled true
/config set ai.providers.grok.enabled false
```

### Configuration Console

```bash
# Launch interactive configuration TUI
/config console

# Provides:
# - Visual editor
# - Validation
# - Save/cancel options
# - Categorized settings
```

### Common Configuration Tasks

#### Change Default AI Provider

```bash
/config set ai.routing.prefer_provider openai
```

#### Adjust Cost Limits

```bash
/config set ai.routing.cost_limit_daily 5.0
```

#### Change Safety Tier

```bash
# More permissive
/config set default_tier 2

# More restrictive
/config set default_tier 3
```

#### Configure Workspace Location

```bash
/config set workspace.root_dir ~/my-workspaces
```

---

## Backup & Restore

### Creating Backups

```bash
# Backup everything
/backup

# Backup specific component
/backup config
/backup session
```

### Restoring Backups

```bash
# List available backups
/restore

# Shows:
# Available backups in ~/.isaac/backups/:
#   backup_2024-11-08.zip (2.3 MB)
#   backup_2024-11-07.zip (2.1 MB)

# Restore specific backup
/restore --file backup_2024-11-08.zip
```

### Backup Workflow

```bash
# Before major changes
/backup

# Make changes
/config set default_tier 1
/workspace create experimental

# If something breaks
/restore --file backup_2024-11-08.zip
```

---

## Advanced Workflows

### Multi-Project Development

```bash
# Setup
/workspace create frontend --venv --collection
/workspace create backend --venv --collection
/workspace create mobile --venv --collection

# Working on frontend
/workspace switch frontend
/mine upload workspace-frontend docs/api.md
npm install
isaac create a new React component

# Switch to backend
/workspace switch backend
pip install -r requirements.txt
/ask how do I implement rate limiting?

# Quick switch
/workspace switch mobile
```

### Code Review Workflow

```bash
# 1. Analyze code
/analyze src/auth.py | /save review_auth.txt

# 2. Find all TODOs
/grep "TODO" **/*.py | /save todos.txt

# 3. Check for security issues
/grep -i "password\|secret\|api.key" **/*.py | /save security_review.txt

# 4. Summarize findings
/read review_auth.txt
/ask summarize the main issues in this code review
```

### Documentation Generation

```bash
# 1. Find all Python modules
/glob "src/**/*.py" | /save modules.txt

# 2. Analyze each module
/analyze src/main.py | /save docs/main.md
/analyze src/utils.py | /save docs/utils.md

# 3. Generate overview
isaac create a README based on the project structure

# 4. Upload to collection for reference
/mine upload project_docs docs/*.md
```

### Automated Testing Setup

```bash
# 1. Create test workspace
/workspace create testing --venv

# 2. Switch to workspace
/workspace switch testing

# 3. Install test framework
pip install pytest pytest-cov

# 4. Create test files
/newfile tests/test_main.py
/newfile tests/test_utils.py

# 5. Configure pytest
/newfile pytest.ini --content "[pytest]\ntestpaths = tests\n"

# 6. Run tests
pytest -v
```

### CI/CD Integration

```bash
# 1. Create CI workspace
/workspace create ci-cd

# 2. Generate GitHub Actions workflow
isaac create a GitHub Actions workflow for Python testing

# 3. Save workflow
/newfile .github/workflows/test.yml

# 4. Add deployment script
/newfile deploy.sh

# 5. Configure for different environments
/workspace create production
/workspace create staging
/workspace create development
```

### Learning New Technology

```bash
# 1. Create learning workspace
/workspace create learn-kubernetes --collection

# 2. Download tutorials
# (manually download docs)

# 3. Upload to collection
/mine upload workspace-learn-kubernetes *.md

# 4. Ask questions with context
/ask explain Kubernetes pods
# AI references your uploaded documentation

# 5. Practice commands
/ask show me how to create a deployment

# 6. Save notes
/newfile notes/pods.md --content "Pod notes..."
```

---

## Tips & Best Practices

### 1. Use Workspaces for Isolation

```bash
# Don't mix projects - create separate workspaces
/workspace create client-project-a --venv --collection
/workspace create client-project-b --venv --collection
```

### 2. Upload Documentation to Collections

```bash
# Better AI assistance with project context
/mine upload workspace-myproject README.md
/mine upload workspace-myproject docs/*.md
```

### 3. Leverage Command Piping

```bash
# Chain operations instead of multiple commands
/read data.txt | /grep "pattern" | /save results.txt
```

### 4. Use Templates for Common Files

```bash
# Add custom templates for your tech stack
/newfile --set-template .go "package main\n\nfunc main() {}\n"
/newfile --set-template .tsx "import React from 'react'\n\n"
```

### 5. Regular Backups

```bash
# Backup before major changes
/backup

# Set up cron/scheduled task for daily backups
0 2 * * * cd /path/to/isaac && /backup
```

### 6. Monitor AI Costs

```bash
# Check usage regularly
/config ai

# Set appropriate limits
/config set ai.routing.cost_limit_daily 5.0
```

---

## Troubleshooting Common Issues

### Issue: AI not responding

```bash
# 1. Check AI status
/config ai

# 2. Verify API keys
/config

# 3. Try different provider
/config set ai.routing.prefer_provider claude

# 4. Check internet connection
ping api.x.ai
```

### Issue: Workspace not switching

```bash
# 1. List workspaces
/workspace list

# 2. Verify workspace exists
ls ~/.isaac/workspaces/

# 3. Recreate if needed
/workspace create myproject
```

### Issue: Unix aliases not working

```bash
# 1. Check if enabled
/alias

# 2. Enable if needed
/alias --enable

# 3. Verify translation
/alias --show ls
```

### Issue: Command piping fails

```bash
# 1. Test each command separately
/read file.txt
/grep "pattern"

# 2. Check command supports stdin
# (refer to command.yaml stdin: true)

# 3. Use alternative approach
/read file.txt > temp.txt
/grep "pattern" temp.txt
```

---

**Now you're equipped with practical knowledge to use Isaac effectively!** 🎯

Next: Read **COMPLETE_REFERENCE.md** for detailed command documentation.
