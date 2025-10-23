#!/usr/bin/env python
# proske.py — Generate ASCII project skeleton tree file

import argparse
import json
import os
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
CFG_PATH = CFG_DIR / "config.json"

DEF_CFG = {
    "project": str(Path.home() / "Projects"),
    "proske_profiles": {
        "py": {
            "ignore_dirs": ["pycache", "venv"],
            "ignore_extensions": [".pyc", ".pyo"],
            "summary_dirs": []
        },
        "web": {
            "ignore_dirs": [],
            "ignore_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
            "summary_dirs": ["images", "assets", "static"]
        }
    },
    "project_history": []
}

def _safe_err(msg):
    """Print error message in red to stderr."""
    try:
        print(Fore.RED + str(msg) + Fore.RESET, file=sys.stderr)
    except Exception:
        pass

def _ensure_cfg_dir():
    """Create config directory if it doesn't exist."""
    CFG_DIR.mkdir(parents=True, exist_ok=True)

def load_cfg():
    """Load and validate config, initializing defaults if needed."""
    if not CFG_PATH.exists():
        _ensure_cfg_dir()
        with CFG_PATH.open("w", encoding="utf-8") as f:
            json.dump(DEF_CFG, f, indent=2)
    try:
        with CFG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Ensure proske_profiles exists
        if "proske_profiles" not in cfg:
            cfg["proske_profiles"] = DEF_CFG["proske_profiles"]
        # Ensure project_history exists
        if "project_history" not in cfg:
            cfg["project_history"] = DEF_CFG["project_history"]
        # Validate current project
        project = Path(cfg.get("project", DEF_CFG["project"])).expanduser()
        if not project.exists():
            print(Fore.YELLOW + f"Project directory {project} does not exist. Creating it." + Fore.RESET)
            project.mkdir(parents=True, exist_ok=True)
        if not os.access(project, os.W_OK):
            _safe_err(f"Project directory {project} is not writable.")
            sys.exit(1)
        return cfg
    except Exception as e:
        _safe_err(f"Error loading config: {e}")
        sys.exit(1)
        
# In proske.py, add load_config from aliaspro and modify generate_ascii_tree
def load_config(project_dir: Path = None):
    """Load and merge suite, global, and project configs."""
    suite_cfg_path = CFG_DIR / "config.json"
    suite_cfg = {}
    if suite_cfg_path.exists():
        try:
            with suite_cfg_path.open("r", encoding="utf-8") as f:
                suite_cfg = json.load(f)
        except Exception as e:
            _safe_err(f"Error loading suite config {suite_cfg_path}: {e}")
            sys.exit(1)
    
    project_dir = Path(project_dir or suite_cfg.get("project", Path.home() / "Projects")).resolve()
    global_cfg = {}
    cfg_path = CFG_DIR / "proman.json"
    if cfg_path.exists():
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                global_cfg = json.load(f)
        except Exception as e:
            _safe_err(f"Error loading global config {cfg_path}: {e}")
            sys.exit(1)
    
    proj_cfg_path = project_dir / ".proman.json"
    proj_cfg = {}
    if proj_cfg_path.exists():
        try:
            with proj_cfg_path.open("r", encoding="utf-8") as f:
                proj_cfg = json.load(f)
        except Exception as e:
            _safe_err(f"Error loading project config {proj_cfg_path}: {e}")
            sys.exit(1)
    
    cfg = suite_cfg.copy()
    cfg.update(global_cfg)
    cfg.update(proj_cfg)
    cfg["project_dir"] = project_dir
    return cfg

def generate_ascii_tree(root_dir: Path, max_depth: int = None, profile: str = None, cfg: dict = None) -> str:
    # Always use the latest ignore rules from DEF_CFG for the selected profile
    latest_profiles = DEF_CFG.get("proske_profiles", {})
    profile_rules = latest_profiles.get(profile, {"ignore_dirs": [], "ignore_extensions": [], "summary_dirs": []}) if profile else {}
    ignore_dirs = profile_rules.get("ignore_dirs", [])
    ignore_extensions = [ext.lower() for ext in profile_rules.get("ignore_extensions", [])]
    summary_dirs = [name.lower() for name in profile_rules.get("summary_dirs", [])]

    def walk_dir(current: Path, prefix: str = "", depth: int = 0) -> list[str]:
        if max_depth is not None and depth > max_depth:
            return []
        
        lines = []
        try:
            entries = sorted(
                [
                    e for e in current.iterdir()
                    if not (
                        e.is_dir() and (
                            e.name.startswith(".") or any(ignore in e.name.lower() for ignore in ignore_dirs)
                        )
                    )
                ],
                key=lambda p: (p.is_file(), p.name.lower())
            )
        except Exception:
            return lines
        
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            new_prefix = prefix + "    " if is_last else prefix + "│   "
            
            if entry.is_dir():
                if entry.name.lower() in summary_dirs:
                    try:
                        file_count = sum(1 for _ in entry.rglob("*") if _.is_file())
                        lines.append(prefix + connector + f"{entry.name}/ ({file_count} files)")
                    except Exception:
                        lines.append(prefix + connector + f"{entry.name}/ (error counting files)")
                else:
                    lines.append(prefix + connector + entry.name + "/")
                    lines.extend(walk_dir(entry, new_prefix, depth + 1))
            else:
                if entry.suffix.lower() in ignore_extensions:
                    continue
                lines.append(prefix + connector + entry.name)
        
        return lines
    
    tree_lines = [root_dir.name + "/"]
    tree_lines.extend(walk_dir(root_dir))
    
    # Append aliases
    cfg = cfg or load_config(root_dir)
    if cfg.get("aliases"):
        tree_lines.append("\nAliases:")
        for name, cmd in sorted(cfg["aliases"].items()):
            tree_lines.append(f"  {name}: {cmd}")
    return "\n".join(tree_lines)

def main():
    """Generate and save or print ASCII project skeleton tree."""
    ap = argparse.ArgumentParser(prog="proske", description="Generate ASCII project skeleton tree file.")
    ap.add_argument("--depth", type=int, default=None, help="Maximum depth for the tree (default: unlimited).")
    ap.add_argument("--force", action="store_true", help="Overwrite existing project_skeleton.txt without prompt.")
    ap.add_argument("--print", action="store_true", help="Print the tree to console instead of writing to file.")
    ap.add_argument("--pro", choices=["py", "web"], default=None, help="Profile to filter tree (e.g., 'py' ignores __pycache__, 'web' summarizes image folders).")
    args = ap.parse_args()

    cfg = load_cfg()
    project = Path(cfg["project"]).resolve()
    
    tree_content = generate_ascii_tree(project, args.depth, args.pro, cfg)
    
    if args.print:
        print(tree_content)
        return
    
    output_file = project / "project_skeleton.md"
    
    if output_file.exists() and not args.force:
        resp = input(f"File {output_file} exists. Overwrite? (y/n): ").strip().lower()
        if resp != "y":
            print(Fore.YELLOW + "Aborted." + Fore.RESET)
            sys.exit(0)
    
    try:
        output_file.write_text(tree_content + "\n", encoding="utf-8")
        print(Fore.GREEN + f"Project skeleton saved to: {output_file}" + Fore.RESET)
    except Exception as e:
        _safe_err(f"Error writing file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()