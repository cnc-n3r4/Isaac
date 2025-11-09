"""
Script Template Manager

Provides common script patterns and templates.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class ScriptTemplateManager:
    """Manages common script templates and patterns."""

    def __init__(self):
        """Initialize template manager."""
        self.templates = self._load_builtin_templates()
        self.custom_templates: Dict[str, Dict[str, Any]] = {}
        self.storage_path = Path.home() / '.isaac' / 'script_templates.json'
        self._load_custom_templates()

    def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by name.

        Args:
            name: Template name

        Returns:
            Template dictionary or None if not found
        """
        # Check custom templates first
        if name in self.custom_templates:
            return self.custom_templates[name]

        # Check built-in templates
        return self.templates.get(name)

    def list_templates(self) -> List[Dict[str, str]]:
        """
        List all available templates.

        Returns:
            List of template info dictionaries
        """
        result = []

        # Built-in templates
        for name, template in self.templates.items():
            result.append({
                'name': name,
                'description': template['description'],
                'category': template['category'],
                'type': 'built-in'
            })

        # Custom templates
        for name, template in self.custom_templates.items():
            result.append({
                'name': name,
                'description': template['description'],
                'category': template.get('category', 'custom'),
                'type': 'custom'
            })

        return result

    def generate_from_template(self, name: str, variables: Optional[Dict[str, str]] = None) -> str:
        """
        Generate a script from a template.

        Args:
            name: Template name
            variables: Variables to substitute in the template

        Returns:
            Generated script
        """
        template = self.get_template(name)
        if not template:
            raise ValueError(f"Template '{name}' not found")

        script = template['script']

        # Substitute variables
        if variables:
            for var, value in variables.items():
                placeholder = f"{{{var}}}"
                script = script.replace(placeholder, value)

        return script

    def add_custom_template(
        self,
        name: str,
        script: str,
        description: str,
        category: str = 'custom',
        variables: Optional[List[str]] = None
    ) -> bool:
        """
        Add a custom template.

        Args:
            name: Template name
            script: Template script (use {var} for variables)
            description: Template description
            category: Template category
            variables: List of variable names

        Returns:
            True if successful
        """
        self.custom_templates[name] = {
            'script': script,
            'description': description,
            'category': category,
            'variables': variables or []
        }

        return self._save_custom_templates()

    def remove_custom_template(self, name: str) -> bool:
        """Remove a custom template."""
        if name in self.custom_templates:
            del self.custom_templates[name]
            return self._save_custom_templates()
        return False

    def _load_builtin_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load built-in templates."""
        return {
            'basic': {
                'description': 'Basic bash script template',
                'category': 'general',
                'script': '''#!/bin/bash
# {description}

set -e  # Exit on error
set -u  # Error on undefined variable

main() {
    # Your code here
    echo "Hello from {script_name}!"
}

main "$@"
''',
                'variables': ['description', 'script_name']
            },

            'backup': {
                'description': 'Backup files to a directory',
                'category': 'utility',
                'script': '''#!/bin/bash
# Backup script

set -e

SOURCE="{source_dir}"
BACKUP_DIR="{backup_dir}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Create backup
echo "Creating backup of $SOURCE..."
tar -czf "$BACKUP_FILE" "$SOURCE"

echo "Backup created: $BACKUP_FILE"

# Optional: Remove old backups (keep last 7 days)
find "$BACKUP_DIR" -name "backup_*.tar.gz" -mtime +7 -delete

echo "Backup complete!"
''',
                'variables': ['source_dir', 'backup_dir']
            },

            'cleanup': {
                'description': 'Clean up old files',
                'category': 'utility',
                'script': '''#!/bin/bash
# Cleanup old files

set -e

TARGET_DIR="{target_dir}"
DAYS_OLD={days_old}
FILE_PATTERN="{file_pattern}"

echo "Cleaning up files in $TARGET_DIR"
echo "Pattern: $FILE_PATTERN"
echo "Older than: $DAYS_OLD days"

# Find and list files to be deleted
FILES=$(find "$TARGET_DIR" -name "$FILE_PATTERN" -mtime +$DAYS_OLD)

if [ -z "$FILES" ]; then
    echo "No files found to delete"
    exit 0
fi

echo "Files to be deleted:"
echo "$FILES"

# Confirm before deletion
read -p "Delete these files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    find "$TARGET_DIR" -name "$FILE_PATTERN" -mtime +$DAYS_OLD -delete
    echo "Files deleted"
else
    echo "Cancelled"
fi
''',
                'variables': ['target_dir', 'days_old', 'file_pattern']
            },

            'deploy': {
                'description': 'Simple deployment script',
                'category': 'deployment',
                'script': '''#!/bin/bash
# Deployment script for {project_name}

set -e

PROJECT_DIR="{project_dir}"
BRANCH="{branch}"

echo "Deploying {project_name}..."

# Navigate to project
cd "$PROJECT_DIR"

# Pull latest changes
echo "Pulling latest changes from $BRANCH..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

# Install dependencies (customize for your project)
echo "Installing dependencies..."
# npm install  # For Node.js
# pip install -r requirements.txt  # For Python
# composer install  # For PHP

# Run tests (optional)
echo "Running tests..."
# npm test
# pytest
# phpunit

# Build (if needed)
echo "Building project..."
# npm run build
# make

# Restart services (customize)
echo "Restarting services..."
# systemctl restart {service_name}
# pm2 restart {app_name}

echo "Deployment complete!"
''',
                'variables': ['project_name', 'project_dir', 'branch']
            },

            'monitor': {
                'description': 'Monitor a service and restart if down',
                'category': 'monitoring',
                'script': '''#!/bin/bash
# Service monitor for {service_name}

SERVICE_NAME="{service_name}"
CHECK_COMMAND="{check_command}"
RESTART_COMMAND="{restart_command}"
LOG_FILE="/var/log/${SERVICE_NAME}_monitor.log"

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# Check if service is running
if $CHECK_COMMAND; then
    log_message "$SERVICE_NAME is running"
    exit 0
else
    log_message "$SERVICE_NAME is down! Attempting restart..."

    # Try to restart
    if $RESTART_COMMAND; then
        log_message "$SERVICE_NAME restarted successfully"

        # Wait a bit and verify
        sleep 5
        if $CHECK_COMMAND; then
            log_message "$SERVICE_NAME confirmed running after restart"
        else
            log_message "ERROR: $SERVICE_NAME failed to start after restart"
            # Send alert (customize)
            # mail -s "$SERVICE_NAME Failed" admin@example.com < "$LOG_FILE"
        fi
    else
        log_message "ERROR: Failed to restart $SERVICE_NAME"
    fi
fi
''',
                'variables': ['service_name', 'check_command', 'restart_command']
            },

            'git-sync': {
                'description': 'Sync multiple git repositories',
                'category': 'git',
                'script': '''#!/bin/bash
# Sync multiple git repositories

set -e

REPOS=(
{repo_list}
)

echo "Syncing ${#REPOS[@]} repositories..."

for REPO in "${REPOS[@]}"; do
    echo ""
    echo "=== Syncing $REPO ==="

    if [ ! -d "$REPO" ]; then
        echo "ERROR: Directory not found: $REPO"
        continue
    fi

    cd "$REPO"

    # Check if it's a git repository
    if [ ! -d ".git" ]; then
        echo "ERROR: Not a git repository: $REPO"
        continue
    fi

    # Get current branch
    BRANCH=$(git branch --show-current)
    echo "Branch: $BRANCH"

    # Check for uncommitted changes
    if ! git diff-index --quiet HEAD --; then
        echo "WARNING: Uncommitted changes in $REPO"
        continue
    fi

    # Pull latest changes
    echo "Pulling latest changes..."
    git pull origin "$BRANCH"

    echo "✓ $REPO synced"
done

echo ""
echo "All repositories synced!"
''',
                'variables': ['repo_list']
            },

            'log-analyzer': {
                'description': 'Analyze log files for errors',
                'category': 'monitoring',
                'script': '''#!/bin/bash
# Log analyzer for {log_file}

LOG_FILE="{log_file}"
ERROR_PATTERN="{error_pattern}"
REPORT_FILE="/tmp/log_analysis_$(date +%Y%m%d_%H%M%S).txt"

echo "Analyzing logs: $LOG_FILE"
echo "Report will be saved to: $REPORT_FILE"

# Create report header
cat > "$REPORT_FILE" << EOF
Log Analysis Report
Generated: $(date)
Log file: $LOG_FILE
Error pattern: $ERROR_PATTERN

================================================================================
EOF

# Count total errors
ERROR_COUNT=$(grep -c "$ERROR_PATTERN" "$LOG_FILE" || echo 0)
echo "Total errors found: $ERROR_COUNT" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Get recent errors (last 20)
echo "Recent errors:" >> "$REPORT_FILE"
echo "================================================================================\n" >> "$REPORT_FILE"
grep "$ERROR_PATTERN" "$LOG_FILE" | tail -20 >> "$REPORT_FILE"

# Error frequency by hour
echo "" >> "$REPORT_FILE"
echo "Error frequency by hour:" >> "$REPORT_FILE"
echo "================================================================================\n" >> "$REPORT_FILE"
grep "$ERROR_PATTERN" "$LOG_FILE" | cut -d' ' -f1-2 | cut -d: -f1 | sort | uniq -c | sort -nr >> "$REPORT_FILE"

# Display report
cat "$REPORT_FILE"

echo ""
echo "Report saved to: $REPORT_FILE"
''',
                'variables': ['log_file', 'error_pattern']
            }
        }

    def _load_custom_templates(self):
        """Load custom templates from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    self.custom_templates = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load custom templates: {e}")
                self.custom_templates = {}

    def _save_custom_templates(self) -> bool:
        """Save custom templates to storage."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w') as f:
                json.dump(self.custom_templates, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving custom templates: {e}")
            return False
