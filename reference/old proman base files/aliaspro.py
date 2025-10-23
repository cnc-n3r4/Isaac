#!/usr/bin/env python
# aliaspro.py — Manage and execute project-scoped command aliases

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from colorama import init as color_init, Fore
    color_init()
except ImportError:
    class _Dummy:
        def __getattr__(self, k): return ""
    Fore = _Dummy()

APP = "newfile"
CFG_DIR = Path(os.getenv("APPDATA") or (Path.home() / ".config")) / APP
CFG_PATH = CFG_DIR / "proman.json"
SUITE_CFG_PATH = CFG_DIR / "config.json"
PROJ_CFG = ".proman.json"

def _safe_err(msg):
    """Print error message in red to stderr."""
    try:
        print(Fore.RED + str(msg) + Fore.RESET, file=sys.stderr)
    except Exception:
        pass

def _ensure_cfg_dir():
    """Create config directory if it doesn't exist."""
    CFG_DIR.mkdir(parents=True, exist_ok=True)

def _load_raw(path: Path) -> dict:
    """Load JSON file, returning empty dict if missing."""
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception as e:
        _safe_err(f"Error loading {path}: {e}")
        sys.exit(1)

def expand_vars(s: str, project_dir: Path) -> str:
    """Expand ${PROJECT_NAME}, ${PROJECT_DIR}, and other environment variables."""
    vars_map = {"PROJECT_NAME": project_dir.name, "PROJECT_DIR": str(project_dir)}
    s = re.sub(r"\$\{([A-Z0-9_]+)\}", lambda m: vars_map.get(m.group(1), m.group(0)), s)
    return os.path.expandvars(s)

# Replace load_config function
def load_config(project_dir: Path = None, read_only: bool = False):
    """Load and merge suite, global, and project configs."""
    suite_cfg = _load_raw(SUITE_CFG_PATH)
    if project_dir is None:
        if "project" in suite_cfg:
            project_dir = Path(suite_cfg["project"]).resolve()
            if not project_dir.exists() and not read_only:
                _safe_err(f"Warning: Configured project directory {project_dir} does not exist. Using current directory.")
                project_dir = Path.cwd()
        else:
            _safe_err(f"Warning: No project directory set in {SUITE_CFG_PATH}. Using current directory.")
            project_dir = Path.cwd()
    else:
        project_dir = Path(project_dir).resolve()
    
    if not read_only:
        if not project_dir.exists():
            _safe_err(f"Project directory {project_dir} does not exist.")
            sys.exit(1)
        if not os.access(project_dir, os.W_OK):
            _safe_err(f"Project directory {project_dir} is not writable.")
            sys.exit(1)

    global_cfg = _load_raw(CFG_PATH)
    proj_cfg = _load_raw(project_dir / PROJ_CFG)
    
    cfg = suite_cfg.copy()
    cfg.update(global_cfg)
    cfg.update(proj_cfg)
    cfg["project_dir"] = project_dir
    return cfg

def save_config(config_aliases: dict, project_dir: Path, use_global: bool):
    """Save aliases to global or project config with backup."""
    target = CFG_PATH if use_global else project_dir / PROJ_CFG
    bak = target.with_name(target.name + ".bak")
    raw = _load_raw(target)
    raw.setdefault("aliases", {})
    for k, v in config_aliases.items():
        if v is None:
            raw["aliases"].pop(k, None)
        else:
            raw["aliases"][k] = v
    try:
        _ensure_cfg_dir()
        if target.exists():
            bak.write_bytes(target.read_bytes())
        target.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        print(Fore.GREEN + f"Saved aliases to {target}" + Fore.RESET)
    except Exception as e:
        _safe_err(f"Error saving {target}: {e}")
        sys.exit(1)

# Update main function to pass read_only flag
def main():
    """Manage and execute project-scoped command aliases."""
    HELP_TEXT = """
    ALIASPRO(1)                          User Commands                          ALIASPRO(1)

    NAME
        aliaspro - Manage and execute project-scoped command aliases.

    SYNOPSIS
        aliaspro [OPTIONS] COMMAND [NAME] [CMD ...]

    DESCRIPTION
        aliaspro manages command aliases for projects, stored in PROJ/.proman.json or
        %APPDATA%\\newfile\\proman.json (global). Aliases simplify repetitive tasks like
        running, testing, or building projects. Wrapper commands (runpro, testpro, buildpro)
        execute predefined aliases.

    COMMANDS
        set NAME CMD ...    Create or update an alias with the given command.
        get NAME            Print the command for an alias.
        del NAME            Delete an alias.
        rename OLD NEW      Rename an alias.
        which NAME          Show the config scope (project or global) for an alias.
        list                List all aliases.
        run NAME [-- ARGS]  Execute an alias, passing additional arguments.

    OPTIONS
        --dir PATH          Project directory (default: config project from %APPDATA%\\newfile\\config.json or current directory).
        --global-config     Use global config (%APPDATA%\\newfile\\proman.json) instead of project config.
        --global            Alias for --global-config.
        --verbose           Print detailed execution information.
        --json              Output in JSON format (for get, list, which).
        --dry-run           Preview actions without executing.
        --yes               Skip confirmation prompts for destructive actions.
        -h, --help          Show this help message.

    CONFIGURATION
        Project config: PROJ/.proman.json
        Global config:  %APPDATA%\\newfile\\proman.json
        Example .proman.json:
            {
              "aliases": {
                "run": "python app.py",
                "test": "pytest -q",
                "build": "pyinstaller --onefile app.py"
              }
            }

    EXAMPLES
        aliaspro set run "python app.py" --dir C:\\Projects\\MyProj
        aliaspro rename run start --dir C:\\Projects\\MyProj
        aliaspro which run --dir C:\\Projects\\MyProj
        aliaspro list --dir C:\\Projects\\MyProj
        runpro --dir C:\\Projects\\MyProj -- --port 8080
        testpro --dir C:\\Projects\\MyProj

    SEE ALSO
        runpro(1), testpro(1), buildpro(1), setpro(1), newfile(1)
    """

    ap = argparse.ArgumentParser(
        prog="aliaspro",
        description="Manage and execute project-scoped command aliases.",
        add_help=False
    )
    ap.add_argument("-h", "--help", action="store_true", help="Show detailed help message.")
    ap.add_argument("command", choices=["set", "get", "del", "rename", "which", "list", "run"], help="Command to execute.")
    ap.add_argument("name", nargs="?", help="Alias name (for set, get, del, rename, which, run).")
    ap.add_argument("cmd", nargs="*", help="Command for set or new name for rename (after name).")
    ap.add_argument("--dir", default=None, help="Project directory (default: config project or current directory).")
    ap.add_argument("--global-config", "--global", action="store_true", help="Use global config instead of project config.")
    ap.add_argument("--verbose", action="store_true", help="Print detailed execution information.")
    ap.add_argument("--json", action="store_true", help="Output in JSON format.")
    ap.add_argument("--dry-run", action="store_true", help="Preview actions without executing.")
    ap.add_argument("--yes", action="store_true", help="Skip confirmation prompts for destructive actions.")
    args = ap.parse_args()

    if args.help:
        print(HELP_TEXT)
        sys.exit(0)

    read_only = args.command in ["get", "list", "which", "run"]
    cfg = load_config(args.dir, read_only)
    project_dir = cfg["project_dir"]

    if "aliases" not in cfg:
        cfg["aliases"] = {}

    try:
        if args.command == "set":
            if not args.name or not args.cmd:
                _safe_err("Alias name and command required for set.")
                sys.exit(2)
            cmd = " ".join(args.cmd)
            if args.dry_run:
                config_type = "global-config" if args.global_config else "project"
                _safe_err(f"Would set alias '{args.name}' to '{cmd}' in {config_type} config.")
            else:
                save_config({args.name: cmd}, project_dir, args.global_config)
            return

        if args.command == "get":
            if not args.name:
                _safe_err("Alias name required for get.")
                sys.exit(2)
            cmd = cfg["aliases"].get(args.name)
            if cmd is None:
                _safe_err(f"Alias '{args.name}' not found.")
                sys.exit(1)
            if args.json:
                print(json.dumps({"name": args.name, "command": cmd}))
            else:
                print(cmd)
            return

        if args.command == "del":
            if not args.name:
                _safe_err("Alias name required for del.")
                sys.exit(2)
            if args.name not in cfg["aliases"]:
                _safe_err(f"Alias '{args.name}' not found.")
                sys.exit(1)
            if not args.yes and not args.dry_run:
                resp = input(f"Delete alias '{args.name}'? (y/n): ").strip().lower()
                if resp != "y":
                    _safe_err("Aborted.")
                    sys.exit(3)
            if args.dry_run:
                config_type = "global-config" if args.global_config else "project"
                _safe_err(f"Would delete alias '{args.name}' from {config_type} config.")
            else:
                save_config({args.name: None}, project_dir, args.global_config)
            return

        if args.command == "rename":
            if not args.name or not args.cmd or len(args.cmd) != 1:
                _safe_err("Old and new alias names required for rename.")
                sys.exit(2)
            new_name = args.cmd[0]
            if args.name not in cfg["aliases"]:
                _safe_err(f"Alias '{args.name}' not found.")
                sys.exit(1)
            if new_name in cfg["aliases"] and not args.yes and not args.dry_run:
                resp = input(f"Overwrite existing alias '{new_name}'? (y/n): ").strip().lower()
                if resp != "y":
                    _safe_err("Aborted.")
                    sys.exit(3)
            if args.dry_run:
                config_type = "global-config" if args.global_config else "project"
                _safe_err(f"Would rename alias '{args.name}' to '{new_name}' in {config_type} config.")
            else:
                cmd = cfg["aliases"].pop(args.name)
                save_config({new_name: cmd}, project_dir, args.global_config)
            return

        if args.command == "which":
            if not args.name:
                _safe_err("Alias name required for which.")
                sys.exit(2)
            if args.name not in cfg["aliases"]:
                _safe_err(f"Alias '{args.name}' not found.")
                sys.exit(1)
            scope = "project" if (project_dir / PROJ_CFG).exists() and args.name in _load_raw(project_dir / PROJ_CFG).get("aliases", {}) else "global"
            if args.json:
                print(json.dumps({"name": args.name, "scope": scope}))
            else:
                print(f"Alias '{args.name}' found in {scope} config.")
            return

        if args.command == "list":
            aliases = cfg["aliases"]
            if not aliases:
                if args.json:
                    print(json.dumps([]))
                else:
                    print("No aliases defined.")
                return
            if args.json:
                print(json.dumps([{"name": k, "command": v} for k, v in sorted(aliases.items())]))
            else:
                print("Aliases:")
                max_name = max(len(k) for k in aliases)
                for name, cmd in sorted(aliases.items()):
                    print(f"  {name:<{max_name}}: {cmd}")
            return

        if args.command == "run":
            if not args.name:
                _safe_err("Alias name required for run.")
                sys.exit(2)
            cmd = cfg["aliases"].get(args.name)
            if cmd is None:
                _safe_err(f"Alias '{args.name}' not found.")
                sys.exit(1)
            extra = args.cmd
            if extra and extra[0] == "--":
                extra = extra[1:]
            if extra:
                cmd = f"{cmd} {' '.join(extra)}"
            cmd = expand_vars(cmd, project_dir)
            if args.verbose:
                _safe_err(f"Executing: {cmd}")
            if args.dry_run:
                _safe_err(f"Would execute: {cmd}")
            else:
                try:
                    if os.name == "nt":
                        result = subprocess.run(
                            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                            check=False, cwd=project_dir
                        )
                    else:
                        result = subprocess.run(["bash", "-lc", cmd], check=False, cwd=project_dir)
                    if result.returncode != 0:
                        _safe_err(f"Command failed with exit code {result.returncode}")
                    sys.exit(result.returncode)
                except subprocess.SubprocessError as e:
                    _safe_err(f"Error executing command: {e}")
                    sys.exit(1)
                except KeyboardInterrupt:
                    _safe_err("Command interrupted by user.")
                    sys.exit(130)

    except (ValueError, KeyError) as e:
        _safe_err(str(e))
        sys.exit(2 if isinstance(e, ValueError) else 1)

if __name__ == "__main__":
    main()