# Natural Language Shell Scripting

A comprehensive system for converting natural language to bash scripts, with generation, explanation, scheduling, and validation capabilities.

## Features

### 1. English to Bash Translation
Convert natural language descriptions into bash commands and scripts.

```bash
/script translate "list all text files in current directory"
/script translate "find files modified in the last 7 days"
/script translate "show disk usage"
```

**Features:**
- AI-powered translation for complex commands
- Pattern-based fallback for common operations
- Caching for frequently used translations
- Safety warnings for destructive operations
- Confidence scoring

### 2. Script Generation
Generate complex, production-ready bash scripts from descriptions.

```bash
/script generate "Create a backup script that archives files daily"
/script generate "Monitor a web service and restart if down"
/script generate "Sync multiple git repositories"
```

**Features:**
- Complete scripts with proper structure
- Error handling and best practices
- Function documentation
- Suggested test cases
- Usage instructions

### 3. Script Explanation
Understand what bash scripts do in plain English.

```bash
/script explain "script.sh"
/script explain "#!/bin/bash\nrm -rf /tmp/*"
```

**Features:**
- Summary of script purpose
- Line-by-line explanations
- Function descriptions
- Complexity analysis
- Potential issues and warnings

### 4. Natural Language Scheduling
Schedule scripts using plain English instead of cron syntax.

```bash
/script schedule "backup.sh" --when "every day at 2pm"
/script schedule "cleanup.sh" --when "every Monday at midnight"
/script schedule "check.sh" --when "every 15 minutes"
```

**Features:**
- Natural language to cron conversion
- Human-readable schedule descriptions
- Next run time calculation
- Crontab integration
- List all scheduled scripts

### 5. Script Templates
Quick start with pre-built templates for common tasks.

```bash
/script list-templates
/script template backup
/script template deploy
```

**Available Templates:**
- **basic**: Basic bash script template
- **backup**: Backup files to directory
- **cleanup**: Clean up old files
- **deploy**: Simple deployment script
- **monitor**: Monitor service and restart if down
- **git-sync**: Sync multiple git repositories
- **log-analyzer**: Analyze log files for errors

### 6. Script Validation
Validate scripts for safety and correctness before running.

```bash
/script validate "script.sh"
/script validate "rm -rf /" --strict
```

**Features:**
- Syntax validation
- Safety checks for dangerous patterns
- Best practice suggestions
- Shellcheck integration (if available)
- Safety scoring (0-100)
- Strict mode for production scripts

## Command Reference

### Translate
Convert natural language to bash.

```bash
/script translate "description" [--output file.sh]
```

**Examples:**
```bash
/script translate "list all PDF files"
/script translate "find large files over 100MB" --output find_large.sh
```

### Generate
Generate complex scripts from descriptions.

```bash
/script generate "description" [--output file.sh]
```

Use `|` to separate description from requirements:
```bash
/script generate "backup script | must handle errors, must be idempotent"
```

**Examples:**
```bash
/script generate "Create a log rotation script"
/script generate "Deploy application | check dependencies, run tests"
```

### Explain
Explain what a script does.

```bash
/script explain <script or file> [--detail-level brief|medium|detailed]
```

**Examples:**
```bash
/script explain "/path/to/script.sh"
/script explain "for i in {1..10}; do echo $i; done" --detail-level detailed
```

### Schedule
Schedule a script using natural language.

```bash
/script schedule "command" --when "schedule description"
```

**Examples:**
```bash
/script schedule "backup.sh" --when "every day at 3am"
/script schedule "/usr/local/bin/cleanup" --when "every Sunday"
/script schedule "python check.py" --when "every 30 minutes"
```

**Supported Schedules:**
- `every X minutes` - e.g., "every 15 minutes"
- `every hour` / `hourly`
- `every day at TIME` / `daily at TIME` - e.g., "every day at 2pm"
- `every WEEKDAY` - e.g., "every Monday"
- `every week on WEEKDAY`
- `every month on DAY`
- `first day of month`
- `last day of month`
- `midnight` / `noon`

### Validate
Validate a script for safety and correctness.

```bash
/script validate <script or file> [--strict]
```

**Examples:**
```bash
/script validate "my_script.sh"
/script validate "rm -rf /tmp/*" --strict
```

### Template
Use a pre-built template.

```bash
/script template <name> [--output file.sh]
```

**Examples:**
```bash
/script template basic --output new_script.sh
/script template backup
```

### List Templates
Show all available templates.

```bash
/script list-templates
```

### List Scheduled
Show all scheduled scripts from crontab.

```bash
/script list-scheduled
```

## Python API

### English to Bash Translator

```python
from isaac.nlscript import EnglishToBashTranslator

translator = EnglishToBashTranslator(ai_router)
result = translator.translate("list all log files")

print(result['bash_code'])      # Generated bash code
print(result['explanation'])    # What it does
print(result['warnings'])       # Safety warnings
print(result['confidence'])     # Confidence score
```

### Script Generator

```python
from isaac.nlscript import ScriptGenerator

generator = ScriptGenerator(ai_router)
result = generator.generate(
    "Create a backup script",
    requirements=["Must handle errors", "Must log actions"],
    output_file=Path("backup.sh")
)

print(result['script'])         # Generated script
print(result['metadata'])       # Script metadata
print(result['tests'])          # Suggested tests
print(result['documentation'])  # Usage docs
```

### Script Explainer

```python
from isaac.nlscript import ScriptExplainer

explainer = ScriptExplainer(ai_router)

# Explain a script
result = explainer.explain(script_text, detail_level='detailed')
print(result['summary'])
print(result['line_by_line'])
print(result['functions'])
print(result['potential_issues'])
print(result['complexity'])

# Explain a file
result = explainer.explain_file(Path("script.sh"))
```

### Natural Language Scheduler

```python
from isaac.nlscript import NaturalLanguageScheduler

scheduler = NaturalLanguageScheduler(ai_router)

# Create schedule
result = scheduler.schedule("backup.sh", "every day at 2pm")
print(result['cron_expression'])
print(result['human_readable'])
print(result['next_run'])

# Add to crontab
scheduler.add_to_crontab("backup.sh", "every day at 2pm", comment="Daily backup")

# List scheduled scripts
scheduled = scheduler.list_scheduled_scripts()
```

### Script Template Manager

```python
from isaac.nlscript import ScriptTemplateManager

manager = ScriptTemplateManager()

# List templates
templates = manager.list_templates()

# Get template
template = manager.get_template('backup')

# Generate from template
script = manager.generate_from_template('backup', {
    'source_dir': '/home/user/data',
    'backup_dir': '/backups'
})

# Add custom template
manager.add_custom_template(
    name='my_template',
    script='#!/bin/bash\necho "{message}"',
    description='My custom template',
    variables=['message']
)
```

### Script Validator

```python
from isaac.nlscript import ScriptValidator

validator = ScriptValidator(ai_router)

# Validate script
result = validator.validate(script_text, strict=False)
print(result['valid'])
print(result['errors'])
print(result['warnings'])
print(result['suggestions'])
print(result['safety_score'])

# Quick safety check
if validator.is_safe_to_run(script_text):
    # Execute script
    pass
```

## Safety Features

The Natural Language Shell Scripting system includes comprehensive safety features:

### Dangerous Pattern Detection
- Recursive deletion from root (`rm -rf /`)
- Fork bombs
- Direct disk operations
- Overly permissive permissions
- Piping URLs to bash
- Hardcoded credentials

### Safety Scoring
Scripts receive a safety score from 0-100:
- **90-100**: Very safe
- **70-89**: Generally safe
- **50-69**: Use with caution
- **Below 50**: Potentially dangerous

### Validation Levels
- **Normal**: Checks syntax and common issues
- **Strict**: Enforces best practices (set -e, set -u, etc.)

### Warnings
All potentially dangerous operations produce warnings:
- 🚨 Critical warnings for extremely dangerous operations
- ⚠️  Standard warnings for risky operations
- 💡 Suggestions for improvements

## Architecture

### Components

```
isaac/nlscript/
├── __init__.py           # Module exports
├── translator.py         # English to Bash translation
├── generator.py          # Script generation
├── explainer.py          # Script explanation
├── scheduler.py          # Natural language scheduling
├── templates.py          # Template management
└── validator.py          # Script validation
```

### Command Integration

```
isaac/commands/script/
├── __init__.py          # Command exports
├── command.yaml         # Command configuration
└── run.py              # Command execution
```

### Data Storage

```
~/.isaac/
├── nlscripts/                    # Generated scripts history
├── script_templates.json         # Custom templates
└── ai_config.json               # AI router configuration
```

## Best Practices

### When Using Translation
1. Review generated scripts before execution
2. Check warnings for dangerous operations
3. Test in safe environment first
4. Use `--output` to save for review

### When Generating Scripts
1. Provide clear, detailed descriptions
2. Specify requirements explicitly
3. Review metadata and tests
4. Validate before deploying

### When Scheduling
1. Test scripts before scheduling
2. Use descriptive comments
3. Monitor first few runs
4. Set up logging

### When Validating
1. Use strict mode for production scripts
2. Address all errors before deployment
3. Consider warnings seriously
4. Install shellcheck for better validation

## Examples

### Complete Workflow

```bash
# 1. Translate natural language to bash
/script translate "backup all log files to /backups" --output backup.sh

# 2. Explain the generated script
/script explain backup.sh

# 3. Validate the script
/script validate backup.sh --strict

# 4. Schedule it to run daily
/script schedule "bash /path/to/backup.sh" --when "every day at 3am"

# 5. List all scheduled scripts
/script list-scheduled
```

### Using Templates

```bash
# List available templates
/script list-templates

# Use backup template
/script template backup --output my_backup.sh

# Edit the script to customize
# Then validate
/script validate my_backup.sh
```

### Complex Script Generation

```bash
# Generate with requirements
/script generate "Web service monitor | check every 60s, restart on failure, send email alerts" --output monitor.sh

# Review and test
/script explain monitor.sh
/script validate monitor.sh

# Deploy
chmod +x monitor.sh
./monitor.sh &
```

## Troubleshooting

### "Could not translate to bash"
- AI router may not be configured
- Try using a template instead
- Provide more specific description

### Validation Fails
- Check syntax errors in output
- Review warnings and suggestions
- Use `--strict` mode for details

### Scheduling Doesn't Work
- Verify cron is installed
- Check crontab permissions
- Test cron expression manually

## Future Enhancements

- [ ] AI-powered schedule optimization
- [ ] Script performance profiling
- [ ] Multi-file script generation
- [ ] Interactive script builder
- [ ] Script refactoring tools
- [ ] Cross-platform compatibility checks
- [ ] Integration with CI/CD pipelines

## Contributing

To add new templates:

```python
from isaac.nlscript import ScriptTemplateManager

manager = ScriptTemplateManager()
manager.add_custom_template(
    name='template_name',
    script='template content',
    description='What it does',
    category='category',
    variables=['var1', 'var2']
)
```

## License

Part of the Isaac project.
