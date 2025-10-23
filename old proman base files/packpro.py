#!/usr/bin/env python
# packpro.py — Package project into ZIP or text for archiving/AI sharing

import argparse
import json
import os
import sys
import shutil
import datetime
from pathlib import Path
from subprocess import run, PIPE

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
PROJ_CFG = ".proman.json"

DEF_TYPES = {
    "python": {
        "exclude_dirs": ["__pycache__", ".venv"],
        "exclude_extensions": [".pyc", ".pyo", ".log"],
        "neat_exclude": ["tests/**", "*.bak", "*.log"]
    },
    "web": {
        "exclude_dirs": ["node_modules", ".git"],
        "exclude_extensions": [".jpg", ".png", ".gif", ".bmp"],
        "neat_exclude": ["assets/images/**", "*.min.js"]
    },
    "auto": {}  # Detect based on files
}

def _safe_err(msg):
    try:
        print(Fore.RED + str(msg) + Fore.RESET, file=sys.stderr)
    except Exception:
        pass

def load_config(project_dir: Path = None):
    try:
        cfg = json.loads(CFG_PATH.read_text(encoding="utf-8")) if CFG_PATH.exists() else {}
        project_dir = Path(project_dir or cfg.get("project", Path.home() / "Projects")).resolve()
        if not project_dir.exists():
            _safe_err(f"Project directory {project_dir} does not exist.")
            sys.exit(1)
        if not os.access(project_dir, os.W_OK):
            _safe_err(f"Project directory {project_dir} is not writable.")
            sys.exit(1)
        cfg["project_dir"] = project_dir
        return cfg
    except Exception as e:
        _safe_err(f"Error loading config: {e}")
        sys.exit(1)

def detect_type(project_dir: Path):
    if (project_dir / "requirements.txt").exists() or any(f.suffix == ".py" for f in project_dir.glob("*")):
        return "python"
    if (project_dir / "package.json").exists() or any(f.suffix in [".html", ".js", ".css"] for f in project_dir.glob("*")):
        return "web"
    return "auto"

def create_psr_log(project_dir: Path, output_dir: Path, timestamp: str, args, processed_files: list, errors: list, interrupted: bool = False):
    psr_file = output_dir / f"packpro_psr_log_{timestamp}.txt"
    command = " ".join(sys.argv)
    with open(psr_file, "w", encoding="utf-8") as f:
        f.write(f"Packpro PSR Log\n")
        f.write("=" * 50 + "\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Command: {command}\n")
        f.write(f"Project Directory: {project_dir}\n")
        f.write(f"Output: {output_dir / f'{project_dir.name}_{timestamp}.{args.format}'}\n")
        f.write(f"Status: {'Interrupted' if interrupted else 'Completed'}\n")
        f.write(f"Files Processed: {len(processed_files)}\n")
        f.write("Arguments:\n")
        for arg, value in vars(args).items():
            f.write(f"  {arg}: {value}\n")
        f.write("\nFiles Included:\n")
        for file_path in processed_files or ["None"]:
            f.write(f"  {file_path}\n")
        f.write("\nErrors/Warnings:\n")
        for error in errors or ["None"]:
            f.write(f"  {error}\n")
        f.write("=" * 50 + "\n")
    if args.verbose:
        _safe_err(f"PSR log saved to: {psr_file}")
    return psr_file

def get_skeleton(project_dir: Path, verbose: bool):
    cmd = [sys.executable, str(project_dir / "proske.py"), "--print"]
    if verbose:
        _safe_err(f"Running: {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True, encoding="utf-8", env=env)
    if result.returncode == 0:
        return result.stdout.strip()
    _safe_err(f"Failed to get skeleton: {result.stderr}")
    return ""
    
def get_stats(project_dir: Path, verbose: bool):
    cmd = [sys.executable, str(project_dir / "statpro.py"), "--json"]
    if verbose:
        _safe_err(f"Running: {' '.join(cmd)}")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True, encoding="utf-8", env=env)
    if result.returncode == 0:
        return json.loads(result.stdout)
    _safe_err(f"Failed to get stats: {result.stderr}")
    return {}

def get_deps(project_dir: Path, verbose: bool):
    cmd = [sys.executable, str(project_dir / "depman.py"), "scan", "--json"]
    if verbose:
        _safe_err(f"Running: {' '.join(cmd)}")
    result = run(cmd, stdout=PIPE, stderr=PIPE, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    _safe_err(f"Failed to get deps: {result.stderr}")
    return {}

def pack_project(project_dir: Path, output_dir: Path, args, pipe_data: str = None):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{project_dir.name}_{timestamp}.{args.format}"
    errors = []
    processed_files = []

    # Load ignore from .proman.json
    proman_path = project_dir / PROJ_CFG
    ignore = json.loads(proman_path.read_text(encoding="utf-8")).get("depman", {}).get("ignore", []) if proman_path.exists() else []
    ignore.append("archives/**")  # Exclude default archive directory
    type_rules = DEF_TYPES.get(args.type, {})
    exclude_dirs = type_rules.get("exclude_dirs", []) + (type_rules.get("neat_exclude", []) if args.neat else [])
    exclude_extensions = type_rules.get("exclude_extensions", [])

    if args.use_gitignore:
        gitignore_path = project_dir / ".gitignore"
        if gitignore_path.exists():
            ignore += [line.strip() for line in gitignore_path.read_text().splitlines() if line.strip() and not line.startswith("#")]

    if args.verbose:
        _safe_err(f"Exclusions: dirs={exclude_dirs}, exts={exclude_extensions}, ignore={ignore}")

    # Collect files
    files = []
    for root, dirs, filenames in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and d != "archives"]
        for f in filenames:
            if f.endswith(tuple(exclude_extensions)):
                continue
            file_path = Path(root) / f
            rel_path = str(file_path.relative_to(project_dir))
            if any(rel_path.startswith(p.replace("**/", "")) for p in ignore):
                continue
            files.append(file_path)

    processed_files = [str(f.relative_to(project_dir)) for f in files]

    if args.format == "txt":
        content = f"# Project: {project_dir.name}\nTimestamp: {timestamp}\nCommand: {' '.join(sys.argv)}\nVersion: 1.0\n\n"
        if args.include_skeleton or pipe_data:
            skeleton = pipe_data or get_skeleton(project_dir, args.verbose)
            content += f"## Project Skeleton\n```\n{skeleton}\n```\n\n"
        if args.include_deps:
            deps = get_deps(project_dir, args.verbose)
            content += f"## Dependencies\n```json\n{json.dumps(deps, indent=2)}\n```\n\n"
        content += "## File Contents\n"
        for file in files:
            if file.suffix in [".py", ".txt", ".json", ".md", ".html", ".js", ".css"]:
                try:
                    file_content = file.read_text(encoding="utf-8")
                    content += f"### {file.relative_to(project_dir)}\n```{file.suffix[1:]}\n{file_content}\n```\n"
                except Exception as e:
                    errors.append(f"Error reading {file}: {e}")
        if args.dry_run:
            _safe_err(f"Dry run: Would write {output_file} with {len(processed_files)} files")
            create_psr_log(project_dir, output_dir, timestamp, args, processed_files, errors)
            return
        output_dir.mkdir(parents=True, exist_ok=True)
        if output_file.exists() and not args.force:
            errors.append(f"File {output_file} exists. Use --force to overwrite.")
            create_psr_log(project_dir, output_dir, timestamp, args, processed_files, errors)
            return
        output_file.write_text(content, encoding="utf-8")
    else:  # zip
        if args.include_skeleton:
            skeleton_file = project_dir / "project_skeleton.txt"
            skeleton_file.write_text(get_skeleton(project_dir, args.verbose))
            files.append(skeleton_file)
            processed_files.append("project_skeleton.txt")
        if args.include_deps:
            deps_file = project_dir / "dependencies.json"
            deps_file.write_text(json.dumps(get_deps(project_dir, args.verbose), indent=2))
            files.append(deps_file)
            processed_files.append("dependencies.json")
        if args.dry_run:
            _safe_err(f"Dry run: Would create {output_file} with {len(processed_files)} files")
            create_psr_log(project_dir, output_dir, timestamp, args, processed_files, errors)
            return
        output_dir.mkdir(parents=True, exist_ok=True)
        if output_file.exists() and not args.force:
            errors.append(f"File {output_file} exists. Use --force to overwrite.")
            create_psr_log(project_dir, output_dir, timestamp, args, processed_files, errors)
            return
        # Custom zip with exclusions
        import zipfile
        from zipfile import ZipFile
        exclude_patterns = ignore + exclude_dirs + [f"*.{ext.lstrip('.')}" for ext in exclude_extensions]
        with ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files_in_dir in os.walk(project_dir):
                # Skip excluded dirs
                dirs[:] = [d for d in dirs if not any(pat in d for pat in exclude_dirs)]
                rel_root = Path(root).relative_to(project_dir)
                for file in files_in_dir:
                    rel_file = rel_root / file
                    skip = False
                    for pat in exclude_patterns:
                        if Path(rel_file).match(pat):
                            skip = True
                            break
                    if not skip:
                        zipf.write(os.path.join(root, file), rel_file)
            # Add extra files (skeleton/deps) if included
            for extra_file in files:
                if extra_file != project_dir / "project_skeleton.txt" and extra_file != project_dir / "dependencies.json":
                    continue  # Only extras were appended earlier
                zipf.write(extra_file, extra_file.relative_to(project_dir))
                processed_files.append(str(extra_file.relative_to(project_dir)))

    create_psr_log(project_dir, output_dir, timestamp, args, processed_files, errors)
    print(Fore.GREEN + f"Packaged: {output_file}" + Fore.RESET)

def show_config(project_dir: Path, type: str):
    cfg = load_config(project_dir)
    print(json.dumps({
        "project_dir": str(project_dir),
        "type": type or detect_type(project_dir),
        "exclude_dirs": DEF_TYPES.get(type, {}).get("exclude_dirs", []),
        "exclude_extensions": DEF_TYPES.get(type, {}).get("exclude_extensions", []),
        "neat_exclude": DEF_TYPES.get(type, {}).get("neat_exclude", [])
    }, indent=2))

def main():
    ap = argparse.ArgumentParser(prog="packpro", description="Package project into ZIP or text for archiving/AI sharing.")
    ap.add_argument("command", choices=["pack", "list", "show"], help="Command to execute.")
    ap.add_argument("--dir", default=None, help="Project directory (default: config project).")
    ap.add_argument("--format", choices=["zip", "txt"], default="zip", help="Output format.")
    ap.add_argument("--output", default=None, help="Output directory (default: project_dir/archives).")
    ap.add_argument("--type", default="auto", choices=["auto", "python", "web"], help="Project type for exclusions.")
    ap.add_argument("--neat", action="store_true", help="Neat mode (minimal exclusions).")
    ap.add_argument("--dirty", action="store_true", help="Dirty mode (full inclusion).")
    ap.add_argument("--include-skeleton", action="store_true", help="Include project skeleton.")
    ap.add_argument("--include-deps", action="store_true", help="Include dependencies.")
    ap.add_argument("--include-stats", action="store_true", help="Include project statistics.")
    ap.add_argument("--use-gitignore", action="store_true", help="Use .gitignore exclusions.")
    ap.add_argument("--dry-run", action="store_true", help="Simulate actions.")
    ap.add_argument("--verbose", action="store_true", help="Print detailed info.")
    ap.add_argument("--pipe", action="store_true", help="Process stdin input.")
    args = ap.parse_args()

    if args.neat and args.dirty:
        _safe_err("Cannot use --neat and --dirty together.")
        sys.exit(1)

    cfg = load_config(args.dir)
    project_dir = cfg["project_dir"]
    output_dir = Path(args.output or project_dir / "archives").resolve()

    try:
        if args.command == "pack":
            pipe_data = sys.stdin.read().strip() if args.pipe else None
            pack_project(project_dir, output_dir, args, pipe_data)
        elif args.command == "list":
            for f in sorted(output_dir.glob(f"{project_dir.name}_*.{{zip,txt}}")):
                print(f)
        elif args.command == "show":
            show_config(project_dir, args.type)
    except Exception as e:
        _safe_err(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()