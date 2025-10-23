# ProMan Suite Integration into Isaac

## Executive Summary
Port complete project management suite (newfile, setpro, proske, depman, packpro) into Isaac as native commands. Transform Isaac from "AI shell wrapper" into "AI-enhanced project management shell."

**Killer feature:** `/projio send` creates portable project snapshots for AI analysis, cloud storage, or email sharing via piping.

## Current State

### Standalone Scripts (5 tools)
```
C:\Scripts\
├── newfile.py    # File/template creation, 700+ lines
├── setpro.py     # Project switcher, 150 lines
├── proske.py     # Skeleton generator, 200 lines
├── depman.py     # Dependency manager, 600+ lines
└── packpro.py    # Project packager, 400+ lines
```

**Common patterns:**
- Shared config system (suite/global/project hierarchy)
- Colorama for terminal output
- JSON-based configs
- argparse CLI interfaces
- Similar error handling patterns

## Target State

### Isaac Command Structure
```
isaac/commands/
├── projio/
│   ├── command.yaml
│   ├── run.py              # Main dispatcher
│   ├── config_manager.py   # Config hierarchy handler
│   ├── template_manager.py # Multi-template system
│   ├── file_creator.py     # newfile logic
│   ├── skeleton.py         # proske logic
│   ├── deps.py             # depman logic
│   └── packager.py         # packpro logic (send subcommand!)
```

**Isaac integration:**
```bash
# File creation
/projio new report.md
/projio new app.py --template .py#2

# Project management
/projio switch ~/Projects/MyApp
/projio skeleton --depth 3
/projio skeleton | /ask "what should I refactor?"

# Dependency management
/projio deps scan --json
/projio deps install --backend uv
/projio deps scan | /ask "are there security issues?"

# Project packaging & sharing (THE KILLER FEATURE)
/projio send | /mine cast -wip
/projio send --neat | /ask "review my code"
/projio send --include-deps | email:jimbob "here's the project"
/projio send --format json | /cloud backup
```

---

## Phase 1: Config System Unification

### 1.1 Merge Config Locations

**Current (proman):**
- `%APPDATA%/newfile/config.json` (suite-level)
- `%APPDATA%/newfile/proman.json` (global)
- `.proman.json` (per-project)

**Target (Isaac):**
- `~/.isaac/config.json` (Isaac main config)
- `~/.isaac/projio/config.json` (projio-specific)
- `.projio.json` (per-project, renamed from .proman.json)

### 1.2 Config Manager Class

**File:** `isaac/commands/projio/config_manager.py`

```python
class ConfigManager:
    """Hierarchical config system for project management"""
    
    def __init__(self, isaac_config_dir: Path):
        self.isaac_dir = isaac_config_dir
        self.projio_dir = isaac_config_dir / "projio"
        self.suite_config_path = self.projio_dir / "config.json"
        self.ensure_dirs()
    
    def load_config(self, project_dir: Path = None) -> dict:
        """Load and merge: suite → global → project configs"""
        suite = self._load_json(self.suite_config_path, DEFAULT_SUITE_CONFIG)
        project_dir = project_dir or Path(suite.get("active_project", Path.home() / "Projects"))
        
        proj_cfg_path = project_dir / ".projio.json"
        project = self._load_json(proj_cfg_path, {})
        
        # Merge hierarchy
        cfg = {**suite, **project}
        cfg["project_dir"] = project_dir
        return cfg
    
    def save_project_config(self, project_dir: Path, config: dict):
        """Save project-specific config"""
        cfg_path = project_dir / ".projio.json"
        self._save_json(cfg_path, config)
    
    def get_project_history(self) -> list[str]:
        """Return list of recent projects"""
        suite = self.load_config()
        return suite.get("project_history", [])
    
    def add_to_history(self, project_path: str):
        """Add project to history (most recent last)"""
        suite = self._load_json(self.suite_config_path, {})
        history = suite.get("project_history", [])
        if project_path in history:
            history.remove(project_path)
        history.append(project_path)
        suite["project_history"] = history[-20:]  # Keep last 20
        self._save_json(self.suite_config_path, suite)
```

**Default config structure:**
```python
DEFAULT_SUITE_CONFIG = {
    "active_project": str(Path.home() / "Projects"),
    "default_ext": ".txt",
    "editor": "",
    "project_history": [],
    "templates": {},  # Migrated from newfile_templates.json
    "proske_profiles": {
        "py": {
            "ignore_dirs": ["__pycache__", ".venv", ".git"],
            "ignore_extensions": [".pyc", ".pyo"],
            "summary_dirs": []
        },
        "node": {
            "ignore_dirs": ["node_modules", ".git"],
            "ignore_extensions": [".log"],
            "summary_dirs": ["assets", "images"]
        }
    },
    "depman": {
        "python": {"backend": "pip", "dev_patterns": ["tests/**", "*.test.*"]},
        "node": {"backend": "npm", "dev_patterns": ["*.test.*", "tests/**"]}
    }
}
```

---

## Phase 2: Template System Migration

### 2.1 Template Manager Class

**File:** `isaac/commands/projio/template_manager.py`

Port from `newfile.py` lines 45-150 (template loading/selection logic):

```python
class TemplateManager:
    """Multi-template system with descriptions and selection"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_mgr = config_manager
    
    def get_template(self, ext: str, selector: str = None) -> str:
        """Get template content for extension
        
        Args:
            ext: File extension (e.g., '.py')
            selector: Optional '#N' (index) or '@desc' (description match)
        
        Returns:
            Template content string
        """
        config = self.config_mgr.load_config()
        templates = config.get("templates", {})
        
        ext_lower = ext.lower()
        template_list = templates.get(ext_lower, [])
        
        if not template_list:
            return ""
        
        # Parse selector
        if selector:
            if selector.startswith("#"):
                idx = int(selector[1:]) - 1
                if 0 <= idx < len(template_list):
                    return template_list[idx].get("body", "")
            elif selector.startswith("@"):
                desc_search = selector[1:].lower()
                for tmpl in template_list:
                    if desc_search in tmpl.get("desc", "").lower():
                        return tmpl.get("body", "")
        
        # Single template or interactive selection
        if len(template_list) == 1:
            return template_list[0].get("body", "")
        
        return self._interactive_select(ext, template_list)
    
    def _interactive_select(self, ext: str, templates: list) -> str:
        """Interactive template selection"""
        print(f"Multiple templates for {ext}:")
        for i, t in enumerate(templates, 1):
            desc = t.get("desc", "") or "(no description)"
            print(f"  {i}. {desc}")
        
        while True:
            choice = input(f"Select 1-{len(templates)}: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(templates):
                    return templates[idx].get("body", "")
    
    def add_template(self, ext: str, content: str, description: str = ""):
        """Add new template variant"""
        config = self.config_mgr.load_config()
        templates = config.get("templates", {})
        
        ext_lower = ext.lower()
        if ext_lower not in templates:
            templates[ext_lower] = []
        
        templates[ext_lower].append({"desc": description, "body": content})
        
        # Save to suite config
        # (Implementation depends on ConfigManager.save_suite_config())
```

---

## Phase 3: Command Implementations

### 3.1 File Creator (newfile → projio new)

**File:** `isaac/commands/projio/file_creator.py`

Port from `newfile.py` lines 200-350 (create_file function):

```python
class FileCreator:
    """Create files with templates and editor integration"""
    
    def __init__(self, config_mgr: ConfigManager, template_mgr: TemplateManager):
        self.config = config_mgr
        self.templates = template_mgr
    
    def create_file(self, name: str, ext: str = None, subdir: str = None, 
                   template_selector: str = None, piped_content: str = None,
                   open_editor: bool = True) -> Path:
        """Create file with template or piped content
        
        Args:
            name: Base filename
            ext: Extension (or use config default)
            subdir: Subdirectory under project root
            template_selector: Template selector ('.py#2' or '.py@flask')
            piped_content: Content from stdin (overrides template)
            open_editor: Open file in editor after creation
        
        Returns:
            Path to created file
        """
        cfg = self.config.load_config()
        project_dir = cfg["project_dir"]
        
        # Resolve extension
        if not ext:
            ext = cfg.get("default_ext", ".txt")
        
        # Build path
        target_dir = project_dir / subdir if subdir else project_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{name}{ext}" if not name.endswith(ext) else name
        filepath = target_dir / filename
        
        # Get content
        if piped_content:
            content = piped_content
        else:
            content = self.templates.get_template(ext, template_selector)
        
        # Write file
        filepath.write_text(content, encoding="utf-8")
        
        # Open in editor
        if open_editor:
            self._open_editor(filepath, cfg)
        
        return filepath
    
    def _open_editor(self, filepath: Path, config: dict):
        """Open file in configured editor"""
        editor = config.get("editor")
        if editor:
            subprocess.Popen([editor, str(filepath)])
        # Fallback logic...
```

### 3.2 Skeleton Generator (proske → projio skeleton)

**File:** `isaac/commands/projio/skeleton.py`

Port from `proske.py` lines 50-120:

```python
class SkeletonGenerator:
    """Generate ASCII project tree"""
    
    def __init__(self, config_mgr: ConfigManager):
        self.config = config_mgr
    
    def generate(self, project_dir: Path, max_depth: int = None, 
                profile: str = None, include_aliases: bool = True) -> str:
        """Generate ASCII tree structure"""
        # Port walk_dir logic from proske.py
        # Use profile rules for filtering
        # Append aliases section if enabled
        pass
```

### 3.3 Dependency Manager (depman → projio deps)

**File:** `isaac/commands/projio/deps.py`

Port from `depman.py` (full file, 630 lines):

```python
class DependencyManager:
    """Scan, install, verify project dependencies"""
    
    def __init__(self, config_mgr: ConfigManager):
        self.config = config_mgr
    
    def scan(self, project_dir: Path, lang: str = "auto") -> dict:
        """Scan for Python/Node dependencies"""
        # Port scan_dependencies() logic
        pass
    
    def install(self, project_dir: Path, backend: str = None, lock: bool = False):
        """Install dependencies via pip/npm/uv/etc"""
        # Port install_dependencies() logic
        pass
    
    def verify(self, project_dir: Path) -> dict:
        """Verify against lockfiles"""
        # Port verify_dependencies() logic
        pass
```

### 3.4 Project Packager (packpro → projio send)

**File:** `isaac/commands/projio/packager.py`

Port from `packpro.py` with **enhanced piping support**:

```python
class ProjectPackager:
    """Archive projects as text blobs for AI/sharing"""
    
    def __init__(self, config_mgr: ConfigManager):
        self.config = config_mgr
    
    def send(self, project_dir: Path = None, format: str = "txt", 
            neat: bool = False, include_skeleton: bool = True, 
            include_deps: bool = False, piped_skeleton: str = None,
            single_file: Path = None) -> dict:
        """Package project as text blob for piping
        
        THE KILLER FEATURE: Creates portable project snapshots
        
        Args:
            project_dir: Project to package (defaults to current/active)
            format: 'txt' (markdown) or 'json' (structured)
            neat: Minimal exclusions (no logs, cache, etc.)
            include_skeleton: Add tree structure
            include_deps: Add dependency list
            piped_skeleton: Use piped skeleton instead of generating
            single_file: Send single file instead of whole project
        
        Returns:
            Blob dict ready for piping
        """
        cfg = self.config.load_config(project_dir)
        
        # Collect files (respecting ignore rules)
        files = self._collect_files(project_dir, neat, cfg)
        
        if format == "json":
            return self._create_json_blob(project_dir, files, include_skeleton, 
                                         include_deps, piped_skeleton)
        else:
            return self._create_text_blob(project_dir, files, include_skeleton,
                                         include_deps, piped_skeleton)
    
    def _create_text_blob(self, project_dir, files, include_skeleton, 
                         include_deps, piped_skeleton) -> dict:
        """Create markdown-formatted text blob"""
        content = f"# Project: {project_dir.name}\n\n"
        
        if include_skeleton:
            skeleton = piped_skeleton or self._generate_skeleton(project_dir)
            content += f"## Structure\n```\n{skeleton}\n```\n\n"
        
        if include_deps:
            deps = self._scan_deps(project_dir)
            content += f"## Dependencies\n```json\n{json.dumps(deps, indent=2)}\n```\n\n"
        
        content += "## Files\n\n"
        for filepath, file_content in files:
            rel_path = filepath.relative_to(project_dir)
            ext = filepath.suffix[1:] if filepath.suffix else "txt"
            content += f"### {rel_path}\n```{ext}\n{file_content}\n```\n\n"
        
        return {
            "kind": "text",
            "content": content,
            "meta": {
                "source_command": "/projio send",
                "project": str(project_dir),
                "file_count": len(files),
                "format": "markdown"
            }
        }
    
    def _create_json_blob(self, project_dir, files, include_skeleton,
                         include_deps, piped_skeleton) -> dict:
        """Create structured JSON blob"""
        data = {
            "project": {
                "name": project_dir.name,
                "path": str(project_dir)
            },
            "files": [
                {
                    "path": str(f[0].relative_to(project_dir)),
                    "content": f[1]
                } for f in files
            ]
        }
        
        if include_skeleton:
            data["skeleton"] = piped_skeleton or self._generate_skeleton(project_dir)
        
        if include_deps:
            data["dependencies"] = self._scan_deps(project_dir)
        
        return {
            "kind": "json",
            "content": data,
            "meta": {
                "source_command": "/projio send",
                "project": str(project_dir),
                "file_count": len(files)
            }
        }
    
    def _collect_files(self, project_dir, neat, cfg):
        """Collect project files respecting ignore rules"""
        # Port from packpro.py pack_project logic
        # Use .projio.json ignore rules + profile defaults
        pass
```

---

## Phase 4: Command Dispatcher

### 4.1 Main Command Entry Point

**File:** `isaac/commands/projio/run.py`

```python
#!/usr/bin/env python
"""
ProMan Suite - Project Management Commands for Isaac
Unified interface for file creation, deps, skeleton, packaging
"""

import sys, json
from pathlib import Path
from isaac.core.session_manager import SessionManager
from .config_manager import ConfigManager
from .template_manager import TemplateManager
from .file_creator import FileCreator
from .skeleton import SkeletonGenerator
from .deps import DependencyManager
from .packager import ProjectPackager

def main():
    """Main dispatcher for /projio commands"""
    
    # Parse from dispatcher envelope or stdin blob
    piped_blob = None
    if not sys.stdin.isatty():
        try:
            input_data = json.loads(sys.stdin.read())
            if "kind" in input_data:
                # Piped blob
                piped_blob = input_data
                command_line = ""  # Will need to parse from args
            else:
                # Dispatcher envelope
                command_line = input_data.get("command", "")
        except:
            command_line = " ".join(sys.argv[1:])
    else:
        command_line = " ".join(sys.argv[1:])
    
    # Initialize managers
    session = SessionManager()
    isaac_config_dir = Path.home() / ".isaac"
    config = ConfigManager(isaac_config_dir)
    templates = TemplateManager(config)
    
    # Parse subcommand
    parts = command_line.split(maxsplit=1)
    if not parts:
        print(json.dumps({"kind": "error", "content": "Usage: /projio <subcommand> [args]"}))
        return
    
    subcommand = parts[0]
    args = parts[1] if len(parts) > 1 else ""
    
    # Route to handler
    if subcommand == "new":
        creator = FileCreator(config, templates)
        # If piped_blob, use content; else use template
        piped_content = piped_blob["content"] if piped_blob else None
        # Parse args, call creator.create_file(piped_content=piped_content)
        pass
    
    elif subcommand == "switch":
        # Project switcher logic
        pass
    
    elif subcommand == "skeleton":
        generator = SkeletonGenerator(config)
        # Parse args, call generator.generate()
        # Output as blob for piping
        pass
    
    elif subcommand == "deps":
        deps = DependencyManager(config)
        # Parse action (scan/install/verify), route accordingly
        pass
    
    elif subcommand == "send":
        packager = ProjectPackager(config)
        
        # Parse flags: -file, -pro, --neat, --include-deps
        import shlex
        args_list = shlex.split(args) if args else []
        
        project_dir = None
        single_file = None
        neat = "--neat" in args_list
        include_deps = "--include-deps" in args_list
        
        # Check for -file flag
        if "-file" in args_list:
            idx = args_list.index("-file")
            if idx + 1 < len(args_list):
                single_file = Path(args_list[idx + 1])
        
        # Check for -pro flag (project by name)
        elif "-pro" in args_list:
            idx = args_list.index("-pro")
            if idx + 1 < len(args_list):
                project_name = args_list[idx + 1]
                # Resolve from history or config
                history = config.get_project_history()
                matches = [p for p in history if project_name.lower() in Path(p).name.lower()]
                if matches:
                    project_dir = Path(matches[0])
                else:
                    print(json.dumps({"kind": "error", "content": f"Project '{project_name}' not found in history"}))
                    return
        
        # Default to active project
        if not project_dir and not single_file:
            project_dir = config.load_config()["project_dir"]
        
        # Handle piped skeleton
        piped_skeleton = piped_blob["content"] if piped_blob and piped_blob["kind"] == "text" else None
        
        blob = packager.send(
            project_dir=project_dir,
            single_file=single_file,
            piped_skeleton=piped_skeleton,
            neat=neat,
            include_deps=include_deps
        )
        print(json.dumps(blob))
    
    else:
        print(json.dumps({"kind": "error", "content": f"Unknown subcommand: {subcommand}"}))

if __name__ == "__main__":
    main()
```

### 4.2 Command Manifest

**File:** `isaac/commands/projio/command.yaml`

```yaml
name: projio
version: 1.0.0
description: Project management suite (files, deps, skeleton, packaging)
author: User + Sarah
stdin: true  # Support piping

subcommands:
  - name: new
    description: Create file with template
    usage: /projio new <filename> [--template EXT#N]
  
  - name: switch
    description: Switch active project
    usage: /projio switch <path>
  
  - name: skeleton
    description: Generate project tree
    usage: /projio skeleton [--depth N] [--profile py|node]
  
  - name: deps
    description: Manage dependencies
    usage: /projio deps <scan|install|verify>
  
  - name: send
    description: Package project as blob for piping
    usage: /projio send [--neat] [--include-deps] [-file PATH] [-pro PROJECT]

examples:
  - /projio new report.md
  - /projio skeleton --depth 3 | /ask "what needs cleanup?"
  - /projio deps scan --json | /save deps.json
  - /projio send | /mine cast -wip
  - /projio send -file "c:\docs\report.md" | /ask "proofread this"
  - /projio send -pro "big-pharma-web-job" | /task later
  - /projio send --neat | /ask "review my code architecture"
  - /projio skeleton | /projio send | email:jimbob "here's the structure"
```

---

## Phase 5: The Killer Workflows

### 5.1 Project → AI Analysis
```bash
# Current project (default)
/projio send | /ask "review this codebase for issues"

# Specific project by name
/projio send -pro "big-pharma-web-job" --include-deps | /ask "security audit"

# Single file review
/projio send -file "c:\docs\spec.md" | /ask "proofread this"

# Focused analysis
/projio send --neat | /ask "suggest architectural improvements"

# Security audit
/projio deps scan | /ask "are there known vulnerabilities?"
```

### 5.2 Project → Cloud Storage
```bash
# Backup to Collections
/projio send --format json | /mine cast project-backup

# Search your own code later
/mine dig "authentication logic" | /ask "how did I implement OAuth?"
```

### 5.3 Project → Email/Share
```bash
# Share current project
/projio send --neat | email:jimbob "here's the project snapshot"

# Share specific project for later
/projio send -pro "client-widget" | /task later

# Share single file
/projio send -file "c:\reports\q4_summary.pdf" | email:boss "quarterly report"

# Create portable archive
/projio send --format json | /save project_snapshot.json
```

### 5.4 Multi-Step Workflows
```bash
# Document → Package → Store
/projio skeleton --depth 2 > structure.md
/projio deps scan --json > deps.json
/projio send --include-deps | /mine cast project-$(date +%Y%m%d)

# Analyze → Refactor → Test
/projio send | /ask "what needs refactoring?" > todo.md
# ... make changes ...
/projio deps verify | /ask "are dependencies still valid?"
```

---

## Phase 6: Migration Path

### 6.1 Config Migration Script

**File:** `isaac/commands/projio/migrate_config.py`

```python
def migrate_proman_to_isaac():
    """Migrate existing proman configs to Isaac structure"""
    old_cfg_dir = Path(os.getenv("APPDATA")) / "newfile"
    isaac_cfg_dir = Path.home() / ".isaac"
    
    # Copy suite config
    old_suite = old_cfg_dir / "config.json"
    if old_suite.exists():
        suite_data = json.loads(old_suite.read_text())
        # Merge into isaac/projio/config.json
    
    # Copy templates
    old_templates = old_cfg_dir / "newfile_templates.json"
    if old_templates.exists():
        # Migrate to projio config templates section
    
    # Find .proman.json files, rename to .projio.json
    for proj_cfg in Path.home().rglob(".proman.json"):
        proj_cfg.rename(proj_cfg.parent / ".projio.json")
```

### 6.2 Backwards Compatibility

Keep standalone scripts working during transition:
- Scripts detect Isaac installation
- If Isaac present: Call Isaac commands
- If Isaac absent: Use standalone logic

---

## Testing Requirements

### Unit Tests
- `tests/test_projio_config.py` - Config hierarchy merging
- `tests/test_projio_templates.py` - Template selection logic
- `tests/test_projio_file_creator.py` - File creation with templates
- `tests/test_projio_skeleton.py` - Tree generation with profiles
- `tests/test_projio_deps.py` - Dependency scanning
- `tests/test_projio_packager.py` - Blob creation, piping

### Integration Tests
- `tests/test_projio_piping.py` - Piping workflows
- `tests/test_projio_send_workflows.py` - send → mine, send → ask chains
- `tests/test_projio_migration.py` - Config migration
- `tests/test_projio_task_mode.py` - Task orchestration

### Coverage Target
≥85% overall, ≥95% for ConfigManager (safety-critical)

---

## Implementation Phases

**Phase 1 (Foundation):** Config system, Template Manager (2-3 days)
**Phase 2 (Core Commands):** File creator, Skeleton generator (2-3 days)
**Phase 3 (Advanced):** Deps manager, Packager with send (3-4 days)
**Phase 4 (Integration):** Piping, Task mode, Testing (2-3 days)
**Phase 5 (Migration):** Config migration script, docs (1-2 days)

**Total estimate:** 10-15 days full-time development

---

## Benefits

1. **Unified workflow** - All project management in Isaac shell
2. **AI enhancement** - Every proman command pipeable to AI
3. **Project mobility** - `/projio send` makes code shareable/analyzable
4. **Task automation** - Multi-step project setup via task mode
5. **Better UX** - Single command syntax, consistent flags
6. **Cleaner code** - Class-based, testable, maintainable
7. **Isaac ecosystem** - Leverages tier system, cloud sync, AI validation
8. **Future-proof** - Email, cloud, webhook integrations via piping

---

## Breaking Changes

1. Config location: `%APPDATA%/newfile` → `~/.isaac/projio`
2. Project config: `.proman.json` → `.projio.json`
3. Command prefix: Standalone → `/projio <subcommand>`
4. Template storage: Separate JSON → Isaac config

**Migration script handles all automatically.**

---

**Status:** READY FOR IMPLEMENTATION
**Priority:** HIGH - Major feature addition
**Dependencies:** None (standalone enhancement)

**Next Steps:**
1. Create `/projio` command directory structure
2. Port ConfigManager + TemplateManager (Phase 1)
3. Implement `send` subcommand first (highest value)
4. Test piping workflows: send → mine, send → ask
5. Port remaining subcommands
6. Create migration script
7. Update documentation

---

**The Vision:**
Isaac becomes the glue between your local projects and AI analysis. `/projio send` turns any project into a portable, pipeable blob that can flow through Isaac's ecosystem - to AI, to cloud storage, to email, to anywhere.</content>
<parameter name="filePath">c:\Projects\Isaac-1\.claude\to_refactor\proman_suite_integration.md