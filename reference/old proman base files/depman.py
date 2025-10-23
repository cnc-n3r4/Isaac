#!/usr/bin/env python
# depman.py — Manage project dependencies (scan, generate, install, verify)

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from pathlib import PurePosixPath
from datetime import datetime

try:
    from colorama import init as color_init, Fore
    color_init()
except ImportError:
    class _Dummy:
        def __getattr__(self, k): return ""
    Fore = _Dummy()

APP = "newfile"
CFG_DIR = Path(os.getenv("APPDATA") or (Path.home() / ".config")) / APP
SUITE_CFG_PATH = CFG_DIR / "config.json"
GLOBAL_CFG_PATH = CFG_DIR / "proman.json"
PROJ_CFG = ".proman.json"

def _safe_err(msg):
    """Print error message in red to stderr."""
    try:
        print(Fore.RED + str(msg) + Fore.RESET, file=sys.stderr)
    except Exception:
        pass

def _load_raw(path: Path) -> dict:
    """Load JSON file, returning empty dict if missing."""
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception as e:
        _safe_err(f"Error loading {path}: {e}")
        sys.exit(1)

def install_dependencies(project_dir: Path, deps: dict, lang: str, backend: str, lock: bool, upgrade: bool, dry_run: bool, verbose: bool):
    """Install dependencies using specified backend."""
    cfg = load_config(project_dir)
    if not deps["dependencies"] and not deps["dev_dependencies"]:
        if verbose:
            _safe_err("No dependencies to install")
        return
    
    lang = deps["language"]  # Use detected lang
    
    if lang == "py":
        backend = backend or cfg.get("depman", {}).get("python", {}).get("backend", "pip")
        manifest_path = project_dir / "requirements.txt"
        generate_manifest(project_dir, deps, lang, save=True, dry_run=dry_run, verbose=verbose, force=True)  # Force for install
        if dry_run:
            return
        cmd = [backend, "install", "-r", str(manifest_path)]
        if upgrade:
            cmd.append("--upgrade")
        try:
            if verbose:
                _safe_err(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=project_dir, check=False)
            if result.returncode != 0:
                _safe_err(f"Install failed with exit code {result.returncode}")
                sys.exit(result.returncode)
            if verbose:
                _safe_err(f"Installed dependencies with {backend}")
            if lock:
                if backend == "pipenv":
                    lock_cmd = ["pipenv", "lock"]
                elif backend == "uv":
                    lock_cmd = ["uv", "pip", "compile", str(manifest_path), "-o", "requirements.lock"]
                else:
                    lock_cmd = None
                if lock_cmd:
                    if verbose:
                        _safe_err(f"Running lock: {' '.join(lock_cmd)}")
                    result = subprocess.run(lock_cmd, cwd=project_dir, check=False)
                    if result.returncode != 0:
                        _safe_err(f"Lock failed with exit code {result.returncode}")
                        sys.exit(result.returncode)
        except subprocess.SubprocessError as e:
            _safe_err(f"Error running {backend}: {e}")
            sys.exit(1)
    
    elif lang == "node":
        backend = backend or cfg.get("depman", {}).get("node", {}).get("backend", "npm")
        manifest_path = project_dir / "package.json"
        generate_manifest(project_dir, deps, lang, save=True, dry_run=dry_run, verbose=verbose, force=True)
        if dry_run:
            return
        cmd = [backend, "install"]
        if verbose:
            _safe_err(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=project_dir, check=False)
        if result.returncode != 0:
            _safe_err(f"Install failed with exit code {result.returncode}")
            sys.exit(result.returncode)
        if verbose:
            _safe_err(f"Installed dependencies with {backend}")
        if lock:
            lock_cmd = [backend, "install", "--package-lock"] if backend == "npm" else [backend, "lock"]
            if verbose:
                _safe_err(f"Running lock: {' '.join(lock_cmd)}")
            result = subprocess.run(lock_cmd, cwd=project_dir, check=False)
            if result.returncode != 0:
                _safe_err(f"Lock failed with exit code {result.returncode}")
                sys.exit(result.returncode)

def load_config(project_dir: Path = None):
    """Load and merge suite, global, and project configs."""
    suite_cfg = _load_raw(SUITE_CFG_PATH)
    project_dir = Path(project_dir or suite_cfg.get("project", Path.home() / "Projects")).resolve()
    
    if not project_dir.exists():
        _safe_err(f"Project directory {project_dir} does not exist.")
        sys.exit(1)
    if not os.access(project_dir, os.W_OK):
        _safe_err(f"Project directory {project_dir} is not writable.")
        sys.exit(1)

    global_cfg = _load_raw(GLOBAL_CFG_PATH)
    proj_cfg = _load_raw(project_dir / PROJ_CFG)
    
    cfg = suite_cfg.copy()
    cfg.update(global_cfg)
    cfg.update(proj_cfg)
    cfg["project_dir"] = project_dir
    return cfg

def scan_dependencies(project_dir: Path, lang: str, exclude: list[str], verbose: bool) -> dict:
    """Scan project for dependencies based on language."""
    cfg = load_config(project_dir)
    profile = lang or "py"
    profile_rules = cfg.get("proske_profiles", {}).get(profile, {"ignore_dirs": [], "ignore_extensions": []}) if profile else {}
    ignore_dirs = [d.lower() for d in profile_rules.get("ignore_dirs", [])]
    exclude_patterns = exclude
    ignore_extensions = [ext.lower() for ext in profile_rules.get("ignore_extensions", [])]
    
    # Detect language
    detected = lang
    if detected == "auto":
        detected = "py" if any(project_dir.rglob("*.py")) or (project_dir / "pyproject.toml").exists() else \
                   "node" if (project_dir / "package.json").exists() or any(project_dir.rglob("*.{js,mjs,cjs,ts,tsx,jsx}")) else "unknown"
        if verbose:
            _safe_err(f"Detected language: {detected}")
    
    deps = {"language": detected, "dependencies": [], "dev_dependencies": [], "timestamp": datetime.now().isoformat()}
    
    if detected == "py":
        dev_patterns = cfg.get("depman", {}).get("python", {}).get("dev_patterns", ["tests/**", "*.test.*"])
        pkg_map = {
            "requests": "requests",
            "numpy": "numpy",
            "pandas": "pandas",
            "flask": "Flask",
            "django": "Django",
            "pytest": "pytest",
            "sqlalchemy": "SQLAlchemy",
            "aiohttp": "aiohttp",
            "telegram": "python-telegram-bot",
            "colorama": "colorama",
            "bs4": "beautifulsoup4",
            "sklearn": "scikit-learn",
            "toml": "toml",
            "matplotlib": "matplotlib",
            "scipy": "scipy",
            "fastapi": "fastapi",
            "pydantic": "pydantic"
        }
        import ast
        import sys
        import toml  # Add this import if not present
        stdlib = set(sys.stdlib_module_names) if hasattr(sys, "stdlib_module_names") else {
            "argparse", "json", "os", "sys", "subprocess", "pathlib", "datetime", "re", "shutil", "shlex",
            "configparser", "getpass", "time", "base64", "hashlib", "logging", "math", "platform", "socket",
            "threading", "traceback", "uuid", "curses", "_curses", "concurrent", "importlib"
        }
        # Read existing manifests
        manifest_deps = set()
        manifest_dev_deps = set()
        requirements_path = project_dir / "requirements.txt"
        if requirements_path.exists():
            try:
                with requirements_path.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pkg = line.split("==")[0].split(">")[0].split("<")[0].strip()
                            if pkg:
                                manifest_deps.add(pkg)
                if verbose:
                    _safe_err(f"Found dependencies from {requirements_path}: {', '.join(manifest_deps)}")
            except Exception as e:
                if verbose:
                    _safe_err(f"Warning: Could not read {requirements_path}: {e}")

        pyproject_path = project_dir / "pyproject.toml"
        if pyproject_path.exists():
            try:
                pyproject = toml.load(pyproject_path)
                project_deps = pyproject.get("project", {}).get("dependencies", [])
                optional_deps = pyproject.get("project", {}).get("optional-dependencies", {})
                for dep in project_deps:
                    pkg = dep.split("==")[0].split(">")[0].split("<")[0].strip()
                    if pkg:
                        manifest_deps.add(pkg)
                for group in optional_deps.values():
                    for dep in group:
                        pkg = dep.split("==")[0].split(">")[0].split("<")[0].strip()
                        if pkg:
                            manifest_dev_deps.add(pkg)
                if verbose:
                    _safe_err(f"Found dependencies from {pyproject_path}: {', '.join(manifest_deps)}")
                    _safe_err(f"Found dev dependencies from {pyproject_path}: {', '.join(manifest_dev_deps)}")
            except Exception as e:
                if verbose:
                    _safe_err(f"Warning: Could not read {pyproject_path}: {e}")
        found_files = False
        scanned_files = []
        for entry in project_dir.rglob("*.py"):
            rel_path = PurePosixPath(entry.relative_to(project_dir).as_posix())
            if any(rel_path.match(p) for p in exclude_patterns) or \
               any(d in [p.lower() for p in entry.parent.parts] for d in ignore_dirs) or \
               entry.suffix.lower() in ignore_extensions:
                if verbose:
                    _safe_err(f"Skipped {entry} (ignored by profile or exclude: {exclude_patterns}, {ignore_dirs}, {ignore_extensions})")
                continue
            found_files = True
            scanned_files.append(entry)
            if verbose:
                _safe_err(f"Scanning file: {entry}")
            try:
                with entry.open("r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                tree = ast.parse(content, filename=str(entry))
                mods = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            mod = alias.name
                            mods.add(mod)
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        mod = node.module
                        mods.add(mod)
                for mod in sorted(mods):
                    if verbose:
                        _safe_err(f"Detected module {mod} in {entry}")
                    top_mod = mod.split('.')[0]
                    if top_mod in stdlib:
                        if verbose:
                            _safe_err(f"Skipped {mod} (standard library)")
                        continue
                    pkg = pkg_map.get(top_mod, top_mod)
                    if pkg:
                        target = "dev_dependencies" if any(entry.match(p) for p in dev_patterns) else "dependencies"
                        if pkg not in deps[target]:
                            deps[target].append(pkg)
                            if verbose:
                                _safe_err(f"Added {pkg} to {target} from {entry}")
                    else:
                        if verbose:
                            _safe_err(f"No package mapping for {mod} (top-level: {top_mod})")
            except SyntaxError as e:
                if verbose:
                    _safe_err(f"Warning: Could not scan {entry}: invalid syntax at {e.filename}:{e.lineno}. Please check the file for errors.")
            except Exception as e:
                if verbose:
                    _safe_err(f"Warning: Could not scan {entry}: {e}")

        if verbose:
            if not found_files:
                _safe_err(f"No Python files found in {project_dir}")
            else:
                _safe_err(f"Scanned {len(scanned_files)} Python files: {', '.join(str(f) for f in scanned_files)}")

        # Merge manifest dependencies
        for pkg in manifest_deps:
            if pkg not in deps["dependencies"] and pkg not in deps["dev_dependencies"]:
                deps["dependencies"].append(pkg)
                if verbose:
                    _safe_err(f"Added {pkg} to dependencies from manifest")
        for pkg in manifest_dev_deps:
            if pkg not in deps["dev_dependencies"] and pkg not in deps["dependencies"]:
                deps["dev_dependencies"].append(pkg)
                if verbose:
                    _safe_err(f"Added {pkg} to dev_dependencies from manifest")


    elif detected == "node":
        dev_patterns = cfg.get("depman", {}).get("node", {}).get("dev_patterns", ["*.test.*", "tests/**"])
        manifest_deps = set()
        manifest_dev_deps = set()
        package_json_path = project_dir / "package.json"
        if package_json_path.exists():
            try:
                pkg = _load_raw(package_json_path)
                manifest_deps.update(pkg.get("dependencies", {}).keys())
                manifest_dev_deps.update(pkg.get("devDependencies", {}).keys())
                if verbose:
                    _safe_err(f"Found dependencies from {package_json_path}: {', '.join(manifest_deps)}")
                    _safe_err(f"Found dev dependencies from {package_json_path}: {', '.join(manifest_dev_deps)}")
            except Exception as e:
                if verbose:
                    _safe_err(f"Warning: Could not read {package_json_path}: {e}")
        
        found_files = False
        scanned_files = []
        for entry in project_dir.rglob("*.{js,mjs,cjs,ts,tsx,jsx}"):
            rel_path = PurePosixPath(entry.relative_to(project_dir).as_posix())
            if any(rel_path.match(p) for p in exclude_patterns) or \
               any(d in [p.lower() for p in entry.parent.parts] for d in ignore_dirs) or \
               entry.suffix.lower() in ignore_extensions:
                if verbose:
                    _safe_err(f"Skipped {entry} (ignored by profile or exclude: {exclude_patterns}, {ignore_dirs}, {ignore_extensions})")
                continue
            found_files = True
            scanned_files.append(entry)
            if verbose:
                _safe_err(f"Scanning file: {entry}")
            try:
                with entry.open("r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                requires = re.findall(r'require\s*\(\s*[\'"]([@a-zA-Z0-9_/-]+)[\'"]\s*\)', content)
                imports_ = re.findall(r'import\s+(?:[^"\']+\s+from\s+)?[\'"]([@a-zA-Z0-9_/-]+)[\'"]', content)
                for pkg in requires + imports_:
                    target = "dev_dependencies" if any(entry.match(p) for p in dev_patterns) else "dependencies"
                    if pkg not in deps[target]:
                        deps[target].append(pkg)
                        if verbose:
                            _safe_err(f"Added {pkg} to {target} from {entry}")
            except Exception as e:
                if verbose:
                    _safe_err(f"Warning: Could not scan {entry}: {e}")
        if verbose:
            if not found_files:
                _safe_err(f"No JavaScript/TypeScript files found in {project_dir}")
            else:
                _safe_err(f"Scanned {len(scanned_files)} JavaScript/TypeScript files: {', '.join(str(f) for f in scanned_files)}")
        
        # Merge manifest dependencies
        for pkg in manifest_deps:
            if pkg not in deps["dependencies"] and pkg not in deps["dev_dependencies"]:
                deps["dependencies"].append(pkg)
                if verbose:
                    _safe_err(f"Added {pkg} to dependencies from package.json")
        for pkg in manifest_dev_deps:
            if pkg not in deps["dev_dependencies"] and pkg not in deps["dependencies"]:
                deps["dev_dependencies"].append(pkg)
                if verbose:
                    _safe_err(f"Added {pkg} to dev_dependencies from package.json")

    return deps         

def verify_dependencies(project_dir: Path, lang: str, verbose: bool) -> dict:
    """Verify dependencies against lockfiles."""
    status = {"verified": True, "issues": [], "timestamp": datetime.now().isoformat()}
    lang = "py" if lang == "auto" else lang  # Default to py
    if lang == "py":
        lockfiles = ["requirements.lock", "Pipfile.lock", "poetry.lock", "uv.lock", "requirements.txt"]
        lockfile = None
        for name in lockfiles:
            candidate = project_dir / name
            if candidate.exists():
                lockfile = candidate
                break
        if lockfile:
            try:
                with lockfile.open("r", encoding="utf-8") as f:
                    content = f.read()
                locked = set()
                if lockfile.name in ["requirements.lock", "requirements.txt"]:
                    locked = set(line.strip().split("==")[0] for line in content.splitlines() if line.strip() and not line.startswith("#"))
                elif lockfile.name == "Pipfile.lock":
                    lock_data = json.loads(content)
                    locked = set(lock_data.get("default", {}).keys()) | set(lock_data.get("develop", {}).keys())
                elif lockfile.name in ["poetry.lock", "uv.lock"]:
                    import toml
                    lock_data = toml.loads(content)
                    locked = set(pkg.get("name", "") for pkg in lock_data.get("package", []))
                deps = scan_dependencies(project_dir, lang, [], False)  # Quiet scan
                missing = set(deps["dependencies"] + deps["dev_dependencies"]) - locked
                if missing:
                    status["verified"] = False
                    status["issues"].extend([f"Missing in lockfile: {dep}" for dep in missing])
                    if verbose:
                        for issue in status["issues"]:
                            _safe_err(issue)
            except Exception as e:
                status["verified"] = False
                status["issues"].append(f"Error reading lockfile {lockfile}: {e}")
                if verbose:
                    _safe_err(status["issues"][-1])
        else:
            if verbose:
                _safe_err("No lockfile found; skipping verification")
    
    elif lang == "node":
        # Basic Node verify (expand as needed)
        lockfile = project_dir / "package-lock.json"
        if lockfile.exists():
            # Parse and compare with package.json deps
            status["issues"].append("Node verification: package-lock.json present (full check TBD)")
        else:
            status["verified"] = False
            status["issues"].append("Missing package-lock.json")
    
    return status
    
def generate_manifest(project_dir: Path, deps: dict, lang: str, save: bool, dry_run: bool, verbose: bool, force: bool = False):
    """Generate dependency manifest (e.g., requirements.txt, package.json)."""
    if verbose:
        _safe_err(f"Generating manifest for {project_dir} (lang={lang}, save={save}, dry_run={dry_run}, force={force})")
    
    lang = deps["language"] if lang == "auto" else lang
    
    if lang == "py":
        manifest_path = project_dir / "requirements.txt"
        content = "# Generated by depman\n"
        if deps["dependencies"]:
            content += "\n".join(sorted(deps["dependencies"])) + "\n"
        if deps["dev_dependencies"]:
            content += "\n# Dev dependencies\n" + "\n".join(sorted(deps["dev_dependencies"])) + "\n"
        if not deps["dependencies"] and not deps["dev_dependencies"]:
            content += "# No dependencies detected\n"
        
        if verbose:
            _safe_err(f"Generated manifest content for {manifest_path}:\n{content}")
        
        if dry_run:
            _safe_err(f"Would write to {manifest_path}")
            return
        
        if save:
            if not os.access(project_dir, os.W_OK):
                _safe_err(f"Permission denied writing to {project_dir}. Check permissions.")
                sys.exit(1)
            
            try:
                if manifest_path.exists() and not force:
                    if verbose:
                        _safe_err(f"Existing file detected: {manifest_path}")
                    resp = input(f"File {manifest_path} exists. Overwrite? (y/n): ").strip().lower()
                    if resp != "y":
                        _safe_err("Aborted manifest write due to user choice.")
                        sys.exit(3)
                    if verbose:
                        _safe_err("User confirmed overwrite")
                
                if verbose:
                    _safe_err(f"Writing manifest to {manifest_path}")
                manifest_path.write_text(content, encoding="utf-8")
                print(Fore.GREEN + f"Saved manifest to {manifest_path}" + Fore.RESET)
            except PermissionError:
                _safe_err(f"Permission denied writing {manifest_path}. Check permissions.")
                sys.exit(1)
            except Exception as e:
                _safe_err(f"Error writing {manifest_path}: {e}")
                sys.exit(1)
        else:
            print(content)
    
    elif lang == "node":
        manifest_path = project_dir / "package.json"
        pkg = _load_raw(manifest_path)
        pkg.setdefault("dependencies", {})
        pkg.setdefault("devDependencies", {})
        for dep in deps["dependencies"]:
            pkg["dependencies"][dep] = ""  # Omit version
        for dep in deps["dev_dependencies"]:
            pkg["devDependencies"][dep] = ""
        if not deps["dependencies"] and not deps["dev_dependencies"]:
            pkg["dependencies"] = pkg.get("dependencies", {})
            pkg["devDependencies"] = pkg.get("devDependencies", {})
        
        content = json.dumps(pkg, indent=2)
        
        if verbose:
            _safe_err(f"Generated manifest content for {manifest_path}:\n{content}")
        
        if dry_run:
            _safe_err(f"Would write to {manifest_path}")
            return
        
        if save:
            if not os.access(project_dir, os.W_OK):
                _safe_err(f"Permission denied writing to {project_dir}. Check permissions.")
                sys.exit(1)
            
            try:
                if manifest_path.exists() and not force:
                    if verbose:
                        _safe_err(f"Existing file detected: {manifest_path}")
                    resp = input(f"File {manifest_path} exists. Overwrite? (y/n): ").strip().lower()
                    if resp != "y":
                        _safe_err("Aborted manifest write due to user choice.")
                        sys.exit(3)
                    if verbose:
                        _safe_err("User confirmed overwrite")
                
                if verbose:
                    _safe_err(f"Writing manifest to {manifest_path}")
                manifest_path.write_text(content, encoding="utf-8")
                print(Fore.GREEN + f"Saved manifest to {manifest_path}" + Fore.RESET)
            except PermissionError:
                _safe_err(f"Permission denied writing {manifest_path}. Check permissions.")
                sys.exit(1)
            except Exception as e:
                _safe_err(f"Error writing {manifest_path}: {e}")
                sys.exit(1)
        else:
            print(content)

def main():
    """Manage project dependencies (scan, generate, install, verify)."""
    HELP_TEXT = """
    DEPMAN(1)                          User Commands                          DEPMAN(1)

    NAME
        depman - Manage project dependencies (scan, generate, install, verify).

    SYNOPSIS
        depman [OPTIONS] COMMAND

    DESCRIPTION
        depman scans project sources to infer dependencies, generates manifests
        (e.g., requirements.txt, package.json), installs dependencies via backends
        (e.g., pip, npm), and verifies lockfiles.

    COMMANDS
        scan                Scan project for dependencies.
        gen                 Generate dependency manifest.
        install             Install dependencies using specified backend.
        verify              Verify dependencies against lockfiles.

    OPTIONS
        --dir PATH          Project directory (default: config project from %APPDATA%\\newfile\\config.json).
        --lang auto|py|node Language to process (default: auto).
        --exclude PATTERN[,..] Patterns to exclude (comma-separated).
        --save              Save generated manifest to file.
        --backend NAME      Backend for install (e.g., pip, npm).
        --lock              Generate lockfile during install.
        --upgrade           Upgrade dependencies during install.
        --verbose           Print detailed execution information.
        --json              Output in JSON format.
        --dry-run           Preview actions without executing.
        -h, --help          Show this help message.

    CONFIGURATION
        Global config: %APPDATA%\\newfile\\proman.json
        Example:
            {
              "depman": {
                "python": { "backend": "pip", "manifest": "requirements.txt" },
                "node": { "backend": "npm", "dev_patterns": ["*.test.*", "tests/**"] },
                "ignore": ["**/.venv/**", "**/node_modules/**"]
              }
            }

    EXAMPLES
        depman scan --dir C:\\Projects\\MyProj --json
        depman gen --save --lang py
        depman install --backend uv --lock
        depman verify --lang node

    SEE ALSO
        statpro(1), proske(1), setpro(1), newfile(1)
    """

    ap = argparse.ArgumentParser(
        prog="depman",
        description="Manage project dependencies (scan, generate, install, verify).",
        add_help=False
    )
    ap.add_argument("-h", "--help", action="store_true", help="Show detailed help message.")
    ap.add_argument("command", choices=["scan", "gen", "install", "verify"], help="Command to execute.")
    ap.add_argument("--dir", default=None, help="Project directory (default: config project).")
    ap.add_argument("--lang", default="auto", choices=["auto", "py", "node"], help="Language to process (default: auto).")
    ap.add_argument("--exclude", default="", help="Patterns to exclude (comma-separated).")
    ap.add_argument("--save", action="store_true", help="Save generated manifest to file (default for gen).")
    ap.add_argument("--force", action="store_true", help="Overwrite manifest without prompting.")
    ap.add_argument("--backend", default=None, help="Backend for install (e.g., pip, npm).")
    ap.add_argument("--lock", action="store_true", help="Generate lockfile during install.")
    ap.add_argument("--upgrade", action="store_true", help="Upgrade dependencies during install.")
    ap.add_argument("--verbose", action="store_true", help="Print detailed execution information.")
    ap.add_argument("--json", action="store_true", help="Output in JSON format.")
    ap.add_argument("--dry-run", action="store_true", help="Preview actions without executing.")
    args = ap.parse_args()

    if args.help:
        print(HELP_TEXT)
        sys.exit(0)

    cfg = load_config(args.dir)
    project_dir = cfg["project_dir"]
    exclude = args.exclude.split(",") if args.exclude else []

    try:
        if args.command == "scan":
            deps = scan_dependencies(project_dir, args.lang, exclude, args.verbose)
            if args.json:
                print(json.dumps(deps, indent=2))
            else:
                print(f"Dependencies for {project_dir} ({deps['language']}):")
                if deps["dependencies"]:
                    print("  Dependencies:")
                    for dep in sorted(deps["dependencies"]):
                        print(f"    {dep}")
                if deps["dev_dependencies"]:
                    print("  Dev Dependencies:")
                    for dep in sorted(deps["dev_dependencies"]):
                        print(f"    {dep}")
            return

        if args.command == "gen":
            deps = scan_dependencies(project_dir, args.lang, exclude, args.verbose)
            generate_manifest(project_dir, deps, deps["language"], save=(not args.dry_run), dry_run=args.dry_run, verbose=args.verbose, force=args.force)
            return
        
        if args.command == "install":
            deps = scan_dependencies(project_dir, args.lang, exclude, args.verbose)
            install_dependencies(project_dir, deps, deps["language"], args.backend, args.lock, args.upgrade, args.dry_run, args.verbose)
            return

        if args.command == "verify":
            status = verify_dependencies(project_dir, args.lang, args.verbose)
            if args.json:
                print(json.dumps(status, indent=2))
            else:
                print(f"Verification for {project_dir} ({args.lang}):")
                print(f"  Verified: {status['verified']}")
                if status["issues"]:
                    print("  Issues:")
                    for issue in status["issues"]:
                        print(f"    {issue}")
            return

    except Exception as e:
        _safe_err(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()