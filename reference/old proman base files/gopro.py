#!/usr/bin/env python
# gopro.py — Go to project directory in PowerShell

import argparse, os, sys, json, subprocess
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

def save_cfg(cfg):
    try:
        _ensure_cfg_dir()
        if CFG_PATH.exists():
            try:
                CFG_BAK.write_bytes(CFG_PATH.read_bytes())
            except Exception as e:
                _safe_err(f"Warning: failed to create backup: {e}")
        with CFG_PATH.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        _safe_err(f"Error saving config: {e}")
        sys.exit(1)

def main():
    ap = argparse.ArgumentParser(prog="gopro", description="Go to the current project directory in PowerShell.")
    ap.add_argument("--print", action="store_true", help="Print the project path instead of launching PowerShell.")
    args = ap.parse_args()

    cfg = load_cfg()
    project = Path(cfg["project"]).resolve()

    if args.print:
        print(str(project))
    else:
        try:
            subprocess.call(['powershell', '-NoExit', '-Command', f"Set-Location '{project}'"])
        except Exception as e:
            _safe_err(f"Error launching PowerShell: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()