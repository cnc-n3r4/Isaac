# Isaac Workspace Management - Isolated Development Environments

## Overview

Isaac workspaces provide isolated, sandboxed environments for your development projects. Each workspace is like a separate folder with its own files, but with additional security controls and management features. Workspaces prevent conflicts between projects and provide a clean separation of concerns.

## Why Use Workspaces?

- **Project Isolation**: Keep different projects completely separate
- **Security Controls**: Sandbox dangerous operations
- **Clean Organization**: No more cluttered directories
- **Easy Switching**: Jump between projects instantly
- **Backup Safety**: Isolated environments prevent cross-contamination

## Quick Start for Beginners

### Step 1: Enable Workspaces
```bash
# Start Isaac
isaac /start

# Open configuration console
isaac /config console

# Navigate to "Workspaces" page
# Enable "Enable workspace isolation and management"
# Set workspace root directory (default: ~/.isaac/workspaces)
# Save settings
```

### Step 2: Create Your First Workspace
```bash
# Create a workspace for your project
isaac workspace create myproject

# Switch to the workspace
isaac workspace switch myproject

# You're now in an isolated environment!
pwd  # Shows workspace directory
```

### Step 3: Work in Your Workspace
```bash
# Create files in the workspace
echo "Hello World" > hello.txt

# Use Isaac commands (they respect workspace boundaries)
isaac /mine --cast *.txt

# Switch between workspaces
isaac workspace switch otherproject
```

## Understanding Workspaces

### What Is a Workspace?
A workspace is:
- **Isolated Directory**: Separate folder for each project
- **Security Sandbox**: Controlled access to system resources
- **Command Context**: Isaac remembers your workspace location
- **File Boundaries**: Operations stay within workspace limits

### Workspace Structure
```
~/.isaac/workspaces/
├── myproject/
│   ├── src/
│   ├── docs/
│   └── notes.txt
├── website/
│   ├── index.html
│   └── assets/
└── research/
    ├── papers/
    └── experiments/
```

## Basic Workspace Commands

### Creating Workspaces
```bash
# Create with default name
isaac workspace create

# Create with specific name
isaac workspace create my-awesome-project

# Create for different purposes
isaac workspace create webapp
isaac workspace create research
isaac workspace create personal
```

### Listing Workspaces
```bash
# Show all your workspaces
isaac workspace list

# Example output:
# Available workspaces:
#   - myproject
#   - webapp
#   - research
```

### Switching Workspaces
```bash
# Switch to a workspace
isaac workspace switch myproject

# Verify you're in the right place
pwd  # Shows workspace directory

# Switch to another workspace
isaac workspace switch webapp
```

### Deleting Workspaces
```bash
# Remove a workspace (CAUTION!)
isaac workspace delete oldproject

# You'll be asked to confirm: "Are you sure? (y/N): y"
```

## Workspace Configuration

### Enabling Workspaces
```bash
# Open configuration console
isaac /config console

# Navigate to Workspaces page
# Check "Enable workspace isolation and management"
# Set root directory (or use default)
# Save and exit
```

### Configuration Options
```bash
# In config console, you can set:
# - Enable/disable workspace system
# - Root directory for all workspaces
# - Integration with sandbox security
```

### Sandbox Integration
Workspaces work with Isaac's sandbox system:
```bash
# Enable sandbox for extra security
isaac /config console
# Go to Sandbox page
# Enable sandbox features
# Configure allowed commands and paths
```

## Working Within Workspaces

### File Operations
```bash
# Switch to workspace
isaac workspace switch myproject

# Create and edit files
touch newfile.txt
echo "content" > file.txt

# Files are automatically in workspace directory
ls  # Shows workspace contents
```

### Isaac Commands in Workspaces
```bash
# /mine searches workspace files
isaac workspace switch myproject
isaac /mine --cast *.txt  # Uploads workspace files
isaac /mine --dig "search workspace content"

# Task mode works within workspace
isaac task: create a simple web page

# All commands respect workspace boundaries
```

### Directory Navigation
```bash
# Workspaces change your working directory
isaac workspace switch project1
pwd  # /home/user/.isaac/workspaces/project1

isaac workspace switch project2
pwd  # /home/user/.isaac/workspaces/project2
```

## Advanced Workspace Features

### Workspace-Specific Settings
```bash
# Each workspace can have different configurations
# Settings are remembered per workspace
# Switch workspaces and settings follow
```

### Integration with Collections
```bash
# Create collection per workspace
isaac workspace switch myproject
isaac /mine --create project-docs

# Upload workspace files
isaac /mine --cast *.md
isaac /mine --cast src/**/*.py
```

### Backup and Recovery
```bash
# Workspaces are self-contained
# Easy to backup entire workspace
cp -r ~/.isaac/workspaces/myproject ~/backups/

# Restore workspace
cp -r ~/backups/myproject ~/.isaac/workspaces/
```

## Security and Sandbox Features

### Sandbox Controls
```bash
# Configure what commands are allowed
isaac /config console
# Sandbox page:
# - Block system paths (/etc, /sys, C:\Windows)
# - Limit file sizes (default: 100MB)
# - Whitelist allowed commands
```

### Path Restrictions
Workspaces prevent access to:
- System directories (`/etc`, `/usr`, `C:\Windows`)
- Other users' files
- Sensitive system areas
- Unauthorized network access

### Command Whitelisting
```bash
# Only approved commands work in sandbox
# Default allowed: pip, npm, git, python, node
# Add more in configuration console
```

## Best Practices

### Organization
1. **One workspace per project**: Keep projects separate
2. **Descriptive names**: `web-app`, `ml-research`, `personal-blog`
3. **Regular cleanup**: Delete unused workspaces
4. **Backup important workspaces**: Copy to external storage

### Workflow
1. **Create workspace**: `isaac workspace create newproject`
2. **Switch to it**: `isaac workspace switch newproject`
3. **Work normally**: Edit files, run commands
4. **Upload to collections**: `isaac /mine --cast *.py`
5. **Switch when done**: `isaac workspace switch otherproject`

### Security
1. **Enable sandbox**: Extra protection for dangerous commands
2. **Use whitelisting**: Only allow needed commands
3. **Regular updates**: Keep workspace isolation enabled
4. **Monitor access**: Check what commands are run

## Examples by Use Case

### Web Development
```bash
# Create web project workspace
isaac workspace create mywebsite

# Switch to workspace
isaac workspace switch mywebsite

# Work on project
touch index.html
mkdir assets
echo "<h1>Hello</h1>" > index.html

# Use allowed commands
npm init
git init
```

### Research Project
```bash
# Create research workspace
isaac workspace create ai-research

# Switch and organize
isaac workspace switch ai-research
mkdir data models notebooks

# Upload research files
isaac /mine --create research-papers
isaac /mine --cast *.pdf
```

### Multiple Projects
```bash
# Create separate workspaces
isaac workspace create frontend
isaac workspace create backend
isaac workspace create mobile

# Switch between them
isaac workspace switch frontend
# Work on frontend code

isaac workspace switch backend
# Work on backend APIs

isaac workspace switch mobile
# Work on mobile app
```

## Troubleshooting

### "Workspace not found" Error
```bash
# Check workspace exists
isaac workspace list

# Create if missing
isaac workspace create missingworkspace

# Check spelling
isaac workspace switch MyProject  # Case sensitive!
```

### "Permission denied" in Workspace
```bash
# Check sandbox settings
isaac /config console
# Sandbox page - check allowed commands

# Add needed commands to whitelist
# Save and try again
```

### Can't Access Files Outside Workspace
```bash
# This is intentional security!
# Copy files into workspace first
cp ~/external/file.txt .
# Then work with them
```

### Workspace Not Persisting
```bash
# Check workspace is enabled
isaac /config console
# Workspaces page - ensure enabled

# Restart Isaac if needed
isaac /exit
isaac /start
```

## Integration with Other Features

### With Collections (/mine)
```bash
# Create workspace-specific collections
isaac workspace switch project1
isaac /mine --create project1-docs

# Search within workspace
isaac /mine --dig "project requirements"
```

### With Task Mode
```bash
# Tasks run in current workspace
isaac workspace switch myapp
isaac task: build the application and run tests
# All files created in workspace
```

### With Keys
```bash
# Keys work across workspaces
isaac --key mykey workspace switch project1
isaac --key mykey /mine --cast file.txt
```

## Performance Considerations

### Workspace Size
- **Keep workspaces focused**: Don't put everything in one workspace
- **Archive old workspaces**: Move completed projects elsewhere
- **Monitor disk usage**: Large workspaces slow down operations

### Command Speed
- **Sandbox overhead**: Security checks add small delay
- **File size limits**: Prevent huge file uploads
- **Command whitelisting**: Faster validation with fewer allowed commands

## Getting Started Checklist

- [ ] Enable workspaces: `isaac /config console` → Workspaces → Enable
- [ ] Create first workspace: `isaac workspace create myfirst`
- [ ] Switch to workspace: `isaac workspace switch myfirst`
- [ ] Create test file: `echo "test" > test.txt`
- [ ] Verify location: `pwd` (should show workspace path)
- [ ] Try Isaac commands: `isaac /mine --cast test.txt`
- [ ] Switch workspaces: `isaac workspace create second` then switch
- [ ] Configure sandbox: Add security restrictions as needed

## Migration from Non-Workspace Setup

### Moving Existing Projects
```bash
# Create workspace for existing project
isaac workspace create oldproject

# Copy files (outside Isaac)
cp -r ~/oldproject/* ~/.isaac/workspaces/oldproject/

# Switch and continue working
isaac workspace switch oldproject
```

### Converting Collections
```bash
# Existing collections still work
# Create workspace-specific collections for new projects
isaac workspace switch newproject
isaac /mine --create newproject-files
```

## Advanced Configuration

### Custom Root Directory
```bash
# Change workspace location
isaac /config console
# Workspaces → Root Directory: /custom/path/workspaces
```

### Sandbox Customization
```bash
# Fine-tune security
isaac /config console
# Sandbox page:
# - Add/remove allowed commands
# - Adjust file size limits
# - Configure path restrictions
```

Workspaces give you the power of isolated development environments with Isaac's security controls. Start small, add workspaces as you need them, and enjoy clean, organized, secure development!</content>
<parameter name="filePath">c:\Projects\Isaac-1\instructions\workspace_management_guide.md