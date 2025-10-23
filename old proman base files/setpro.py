#!/usr/bin/env python
# setpro.py — Set project directory for newfile.py with history

import argparse, os, sys, json
from pathlib import Path

try:
    from colorama import init as color_init, Fore
    color_init()
except Exception:
    class _Dummy:
        def __getattr__(self, k): return ""
    Fore = _Dummy()

APP = "newfile"
CFG_DIR = Path(os.getenv("APPDATA") or (Path.home() / ".config")) / APP
CFG_PATH = CFG_DIR / "config.json"
CFG_BAK  = CFG_DIR / "config.json.bak"

DEF_CFG = {
    "project": str(Path.home() / "Projects"),
    "default_ext": ".txt",
    "ask_type": False,
    "editor": "",
    "project_history": []
}

def _safe_err(msg): 
    try: print(Fore.RED + str(msg) + Fore.RESET, file=sys.stderr)
    except Exception: pass

def _ensure_cfg_dir():
    CFG_DIR.mkdir(parents=True, exist_ok=True)

def load_cfg():
    if not CFG_PATH.exists():
        _ensure_cfg_dir()
        save_cfg(DEF_CFG)
    try:
        with CFG_PATH.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        # Ensure project_history exists
        if "project_history" not in cfg:
            cfg["project_history"] = []
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

# In setpro.py, replace save_cfg function
def save_cfg(cfg):
    try:
        _ensure_cfg_dir()
        if CFG_PATH.exists():
            CFG_BAK.write_bytes(CFG_PATH.read_bytes())
        with CFG_PATH.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        # Create .proman.json if missing
        proj_cfg_path = Path(cfg["project"]) / ".proman.json"
        if not proj_cfg_path.exists():
            with proj_cfg_path.open("w", encoding="utf-8") as f:
                json.dump({"aliases": {}}, f, indent=2)
            print(Fore.GREEN + f"Initialized {proj_cfg_path}" + Fore.RESET)
    except Exception as e:
        _safe_err(f"Error saving config: {e}")
        sys.exit(1)

def validate_project(project: Path):
    if not project.exists():
        print(Fore.YELLOW + f"Project directory {project} does not exist. Creating it." + Fore.RESET)
        project.mkdir(parents=True, exist_ok=True)
    if not os.access(project, os.W_OK):
        _safe_err(f"Project directory {project} is not writable.")
        sys.exit(1)

def main():
    ap = argparse.ArgumentParser(prog="setpro", description="Set project directory for newfile.py with cataloged history.")
    ap.add_argument("--dir", metavar="PATH", help="Set project to this directory and add/update in history.")
    ap.add_argument("--ch", metavar="N", type=int, help="Set project to history item N (1-based index).")
    ap.add_argument("--show", action="store_true", help="Show cataloged history of project directories.")
    args = ap.parse_args()

    cfg = load_cfg()

    set_done = False

    if args.dir:
        project = Path(args.dir).expanduser()
        validate_project(project)
        path_str = str(project)
        history = cfg["project_history"]
        if path_str in history:
            history.remove(path_str)
        history.append(path_str)
        cfg["project"] = path_str
        save_cfg(cfg)
        print(Fore.GREEN + f"Set project to: {path_str}" + Fore.RESET)
        set_done = True

    elif args.ch:
        history = cfg["project_history"]
        if not history:
            _safe_err("No project history available.")
            sys.exit(1)
        n = args.ch
        if not 1 <= n <= len(history):
            _safe_err(f"Invalid history index: {n} (must be 1 to {len(history)})")
            sys.exit(1)
        path_str = history[n-1]
        project = Path(path_str)
        validate_project(project)
        history.remove(path_str)
        history.append(path_str)
        cfg["project"] = path_str
        save_cfg(cfg)
        print(Fore.GREEN + f"Set project to: {path_str}" + Fore.RESET)
        set_done = True

    if args.show:
        history = cfg["project_history"]
        if not history:
            print("No project history.")
        else:
            print("Cataloged project history:")
            for i, p in enumerate(history, 1):
                name = Path(p).name
                print(f"{name}, {i}")
    elif not set_done:
        # No args or just show current
        print(cfg["project"])

if __name__ == "__main__":
    main()