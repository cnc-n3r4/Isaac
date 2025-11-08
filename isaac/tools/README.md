# Isaac Tools

Cross-platform file operation tools for Isaac AI assistant.

## Architecture

All tools inherit from `BaseTool` abstract base class and implement:
- `name`: Tool identifier
- `description`: Human-readable description
- `execute(**kwargs)`: Main execution method
- `get_parameters_schema()`: JSON schema for AI tool calling

## Available Tools

### File Operations (`file_ops.py`)

#### ReadTool
Read file contents with line numbers and offset/limit support.

**Parameters:**
- `file_path` (str, required): Path to file
- `offset` (int, optional): Skip first N lines (default: 0)
- `limit` (int, optional): Read only N lines (default: all)

**Returns:**
```python
{
    'success': bool,
    'content': str,  # Formatted with line numbers
    'error': str,
    'path': str,
    'lines_read': int,
    'total_lines': int
}
```

#### WriteTool
Create files with automatic parent directory creation.

**Parameters:**
- `file_path` (str, required): Path to file
- `content` (str, required): File content
- `overwrite` (bool, optional): Overwrite if exists (default: False)

**Returns:**
```python
{
    'success': bool,
    'content': str,  # Success message
    'error': str,
    'path': str,
    'bytes_written': int
}
```

#### EditTool
Exact string replacement in files.

**Parameters:**
- `file_path` (str, required): Path to file
- `old_string` (str, required): Text to find
- `new_string` (str, required): Replacement text
- `replace_all` (bool, optional): Replace all occurrences (default: False)

**Returns:**
```python
{
    'success': bool,
    'content': str,  # Result message
    'error': str,
    'path': str,
    'replacements': int
}
```

### Code Search (`code_search.py`)

#### GrepTool
Powerful regex search across files with context lines.

**Parameters:**
- `pattern` (str, required): Regex pattern
- `path` (str, optional): Directory to search (default: cwd)
- `glob` (str, optional): File pattern filter (e.g., "*.py")
- `ignore_case` (bool, optional): Case-insensitive (default: False)
- `context` (int, optional): Context lines before/after (default: 0)
- `output_mode` (str, optional): "files" | "content" | "count" (default: "files")

**Returns:**
```python
{
    'success': bool,
    'matches': list,  # Format depends on output_mode
    'error': str,
    'pattern': str,
    'files_searched': int
}
```

#### GlobTool
File pattern matching with metadata.

**Parameters:**
- `pattern` (str, required): Glob pattern (e.g., "**/*.py")
- `path` (str, optional): Directory to search (default: cwd)

**Returns:**
```python
{
    'success': bool,
    'files': [
        {
            'path': str,  # Relative path
            'absolute_path': str,
            'size': int,  # Bytes
            'modified': float  # Unix timestamp
        }
    ],
    'count': int,
    'pattern': str
}
```

## Command Wrappers

Each tool has a corresponding command wrapper in `isaac/commands/`:
- `/read` - ReadTool wrapper
- `/write` - WriteTool wrapper
- `/edit` - EditTool wrapper
- `/grep` - GrepTool wrapper
- `/glob` - GlobTool wrapper

Command wrappers provide:
- CLI argument parsing via argparse
- JSON envelope format for dispatcher
- Help text and examples
- Integration with Isaac's command architecture

## Cross-Platform Compatibility

All tools use `pathlib.Path` for cross-platform file operations.
- Automatic path expansion (`~` to home directory)
- Absolute path resolution
- Parent directory creation
- Platform-agnostic path separators

Tested on:
- ✅ Linux (Ubuntu/Debian)
- ⏳ Windows (PowerShell)
- ⏳ macOS

## AI Integration

All tools provide JSON schemas compatible with:
- Claude API tool calling
- OpenAI function calling
- xAI Grok tool integration

Example schema format:
```python
{
    "type": "function",
    "function": {
        "name": "read",
        "description": "Read file contents with line numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to file"
                }
            },
            "required": ["file_path"]
        }
    }
}
```

## Usage Examples

### Direct Tool Usage
```python
from isaac.tools import ReadTool, GrepTool

# Read file
tool = ReadTool()
result = tool.execute(file_path="app.py", offset=100, limit=50)
print(result['content'])

# Search code
grep = GrepTool()
result = grep.execute(
    pattern=r"class.*Error",
    glob="*.py",
    output_mode="content",
    context=2
)
for match in result['matches']:
    print(match)
```

### Via Command Wrappers
```bash
# Activate venv
source venv/bin/activate

# Read file
python isaac/commands/read/run.py app.py --offset 100 --limit 50

# Search code
python isaac/commands/grep/run.py "class.*Error" --glob "*.py" --output content --context 2

# Find files
python isaac/commands/glob/run.py "**/*.py"
```

### Via Isaac CLI (future)
```bash
isaac /read app.py --offset 100 --limit 50
isaac /grep "TODO" --glob "*.py"
isaac /glob "**/*.js"
```

## Development

### Adding New Tools

1. Create tool class inheriting from `BaseTool`:
```python
from isaac.tools.base import BaseTool

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "mytool"

    @property
    def description(self) -> str:
        return "My tool description"

    def execute(self, **kwargs) -> Dict[str, Any]:
        # Implementation
        return {
            'success': True,
            'content': 'result',
            'error': ''
        }

    def get_parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
```

2. Add to `__init__.py`:
```python
from .mytool import MyTool
__all__ = [..., 'MyTool']
```

3. Create command wrapper in `isaac/commands/mytool/`:
   - `command.yaml` - Metadata and examples
   - `run.py` - CLI argument parsing and tool execution

4. Test thoroughly on all platforms

## Future Enhancements

- [ ] Async tool execution for long-running operations
- [ ] Streaming output for large files
- [ ] Binary file handling improvements
- [ ] Diff/patch tools for code modifications
- [ ] AST-based code transformation tools
- [ ] Project-wide refactoring tools
- [ ] Code quality analysis tools
- [ ] Git integration tools
