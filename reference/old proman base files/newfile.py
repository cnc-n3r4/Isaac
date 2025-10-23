#!/usr/bin/env python
# newfile.py — quick file/project helper
# Changes in this version:
# - Templates stored in %APPDATA%/newfile/newfile_templates.json as a map: ".ext" -> [ { "desc": "...", "body": "..." }, ... ]
#   (Backwards compatible with older formats: string or single object. They get normalized to the new list format.)
# - --settemplate EXT CONTENT [--desc TEXT]     (inline or fromfile:PATH; optional description)
# - --settemplates-json PATH [--overwrite-templates]
# - --settemplates-dir PATH  [--overwrite-templates]  (bulk-load files in a folder as templates; file name == extension)
# - --listtemplates           (shows extension and descriptions with indices)
# - Interactive selection when multiple templates exist for an extension.
#   Also supports --template selectors: ".py#2" (by index, 1-based) or ".py@desc_substring" (by description match).
# - Other existing features kept: project config, default ext, ask-type, editor detection, dry-run, force, print, verbose, colors.

import argparse, os, sys, json, datetime, shutil, subprocess, shlex
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
CFG_TEMPLATES = CFG_DIR / "newfile_templates.json"

DEF_CFG = {
    "project": str(Path.home() / "Projects"),
    "default_ext": ".txt",
    "ask_type": False,
    "editor": ""
}

DEF_TEMPLATES = {
    ".py":   [{"desc": "Python starter", "body": "#!/usr/bin/env python\nif __name__=='__main__':\n    print('hello')\n"}],
    ".txt":  [{"desc": "Plain notes", "body": "# Notes\n"}],
    ".md":   [{"desc": "Markdown doc", "body": "# Markdown Document\n"}],
    ".json": [{"desc": "Basic JSON", "body": "{\n  \"name\": \"new_project\"\n}\n"}],
    ".html": [{"desc": "HTML skeleton", "body": "<!DOCTYPE html>\n<html>\n<head>\n  <meta charset=\"utf-8\" />\n  <title>New File</title>\n</head>\n<body>\n</body>\n</html>\n"}]
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
        # validate project
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
        tmp = CFG_DIR / ("config.json.tmp_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"))
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        tmp.replace(CFG_PATH)
    except Exception as e:
        _safe_err(f"Error saving config: {e}")
        sys.exit(1)

def _normalize_template_value(val):
    """Return list[{'desc','body'}] from legacy forms: str | {'body',...} | list[...]"""
    if isinstance(val, list):
        out = []
        for item in val:
            if isinstance(item, str):
                out.append({"desc": "", "body": item})
            elif isinstance(item, dict):
                body = item.get("body")
                if body is None and "desc" not in item and len(item)==1:
                    # odd case: {'some': 'value'}
                    body = ""
                out.append({"desc": item.get("desc",""), "body": body or ""})
        return out
    if isinstance(val, str):
        return [{"desc": "", "body": val}]
    if isinstance(val, dict):
        return [{"desc": val.get("desc",""), "body": val.get("body","")}]
    return [{"desc": "", "body": ""}]

def load_templates():
    if not CFG_TEMPLATES.exists():
        _ensure_cfg_dir()
        save_templates(DEF_TEMPLATES)
        return DEF_TEMPLATES
    try:
        with CFG_TEMPLATES.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            print(Fore.YELLOW + "Invalid templates file; resetting to defaults." + Fore.RESET)
            save_templates(DEF_TEMPLATES)
            return DEF_TEMPLATES
        norm = {}
        for k, v in raw.items():
            ext = norm_ext(k)
            if not ext: 
                continue
            norm[ext.lower()] = _normalize_template_value(v)
        return norm
    except Exception as e:
        _safe_err(f"Error loading templates: {e}; using defaults.")
        return DEF_TEMPLATES

def save_templates(templates):
    try:
        _ensure_cfg_dir()
        # ensure normalized
        norm = {}
        for k, v in templates.items():
            ext = norm_ext(k)
            if not ext: 
                continue
            norm[ext.lower()] = _normalize_template_value(v)
        tmp = CFG_DIR / ("newfile_templates.tmp_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f"))
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(norm, f, indent=2)
        tmp.replace(CFG_TEMPLATES)
    except Exception as e:
        _safe_err(f"Error saving templates: {e}")

def norm_ext(ext):
    if ext is None: return None
    ext = str(ext).strip()
    if not ext: return None
    return ext if ext.startswith(".") else f".{ext}"

def ensure_dir(p: Path, verbose=False):
    try:
        p.mkdir(parents=True, exist_ok=True)
        if verbose: print(f"Created directory: {p}")
    except Exception as e:
        _safe_err(f"Error creating directory {p}: {e}")
        sys.exit(1)

def _select_editor(cfg, open_with: str | None, verbose=False):
    choices = []
    if open_with: choices.append(open_with)
    if cfg.get("editor"): choices.append(cfg.get("editor"))
    for env_name in ("EDITOR", "VISUAL"):
        v = os.getenv(env_name)
        if v: choices.append(v)
    if os.name == "nt":
        choices.extend(["code", "notepad", "notepad++", "uedit64", "sublime_text", "gvim"])
    else:
        choices.extend(["code", "nano", "vim", "vi", "gedit", "subl", "gvim"])
    for cand in choices:
        s = cand.strip().strip('"').strip("'")
        if (" " in s or s.lower().endswith(".exe")) and os.path.isfile(s):
            if verbose: print(f"Selected editor: {s}")
            return [s]
        parts = shlex.split(s)
        if not parts: 
            continue
        exe = shutil.which(parts[0]) or parts[0]
        if verbose: print(f"Selected editor: {exe} {' '.join(parts[1:])}")
        return [exe, *parts[1:]]
    return None

def _ext_from_dir_entry(name: str):
    # Accept: ".py", "py", "py.tmpl", ".py.tmpl" -> ".py"
    s = name.lstrip(".")
    base = s.split(".", 1)[0]
    if not base: return None
    return "." + base

def _choose_template_interactive(ext: str, items: list[dict]):
    print(f"Multiple templates available for {ext}:")
    for i, t in enumerate(items, 1):
        desc = t.get("desc", "") or "(no description)"
        print(f"  {i}. {desc}")
    while True:
        sel = input(f"Choose 1-{len(items)} (or blank to cancel): ").strip()
        if sel == "": 
            print("Aborted."); sys.exit(3)
        if sel.isdigit():
            n = int(sel)
            if 1 <= n <= len(items):
                return items[n-1]["body"]
        print("Invalid selection.")

def _resolve_template_text(templates: dict, ext_lower: str, template_flag: str | None, verbose=False):
    # Helper to filter list by desc substring (case-insensitive)
    def find_by_desc(lst, needle):
        nlow = needle.lower()
        for item in lst:
            if (item.get("desc","")).lower().find(nlow) >= 0:
                return item
        return None

    # parse selector forms like ".py#2" or ".py@cli"
    selector_index = None
    selector_desc  = None
    if template_flag and not template_flag.lower().startswith("fromfile:"):
        # allow suffix #N and @desc
        # break off any of these from the right hand
        val = template_flag.strip()
        if "#" in val:
            try:
                base, idx = val.rsplit("#", 1)
                template_flag = base
                selector_index = int(idx)
            except Exception:
                pass
        if "@" in template_flag:
            base, key = template_flag.split("@", 1)
            template_flag = base
            selector_desc = key.strip()

    if template_flag:
        t = template_flag.strip()
        if t.lower().startswith("fromfile:"):
            path = t.split(":", 1)[1].strip().strip('"').strip("'")
            file_path = Path(path).expanduser()
            try:
                content = file_path.read_text(encoding="utf-8")
                if verbose: print(f"Loaded template from file: {file_path}")
                return content
            except Exception as e:
                _safe_err(f"Error reading template file '{file_path}': {e}")
                sys.exit(2)
        else:
            t_ext = norm_ext(t)
            if not t_ext:
                _safe_err("Invalid --template value. Use an extension like .py or fromfile:<path>.")
                sys.exit(2)
            lst = templates.get(t_ext.lower(), [])
            lst = _normalize_template_value(lst)
            if not lst:
                return ""
            if selector_index:
                if 1 <= selector_index <= len(lst):
                    return lst[selector_index-1].get("body","")
            if selector_desc:
                m = find_by_desc(lst, selector_desc)
                if m: return m.get("body","")
            if len(lst) == 1:
                return lst[0].get("body","")
            # interactive
            return _choose_template_interactive(t_ext, lst)

    # no explicit template flag: use ext default list
    lst = templates.get(ext_lower, [])
    lst = _normalize_template_value(lst)
    if not lst:
        return ""
    if len(lst) == 1:
        return lst[0].get("body","")
    # interactive
    return _choose_template_interactive(ext_lower, lst)

def create_file(cfg, templates, name, ext=None, subdir=None, open_with=None, template=None, print_only=False, force=False, dry_run=False, verbose=False):
    base = Path(cfg["project"]).expanduser()
    if subdir: base = base / Path(subdir)
    ensure_dir(base, verbose)

    if ext and ext.lower() == "off": ext = None
    ext = norm_ext(ext)
    if not ext:
        if cfg.get("ask_type", False):
            ext = norm_ext(input("File extension (e.g. .py): ").strip())
            if not ext:
                print(Fore.RED + "No extension provided. Aborting." + Fore.RESET)
                sys.exit(2)
        else:
            ext = cfg.get("default_ext") or ".txt"
            if verbose: print(f"Using default extension: {ext}")

    if not name:
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"new_{stamp}"
    filename = f"{name}{ext}" if not str(name).lower().endswith(ext.lower()) else name
    target = (base / filename).resolve()

    if target.exists():
        if dry_run:
            print(f"[DRY-RUN] Exists: {target}")
            if print_only: print(str(target))
            return target
        if not force:
            resp = input(f"File {target} exists. Overwrite? (y/n): ").strip().lower()
            if resp != "y":
                print(Fore.YELLOW + "Aborted." + Fore.RESET)
                sys.exit(3)
        if verbose: print(f"Overwriting existing file: {target}")

    if dry_run:
        print(f"[DRY-RUN] Would create: {target}")
        if print_only: print(str(target))
        return target

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        content = _resolve_template_text(templates, ext_lower=ext.lower(), template_flag=template, verbose=verbose)
        if content:
            with target.open("w", encoding="utf-8", newline="\n") as f:
                f.write(content)
        else:
            target.touch()
    except Exception as e:
        _safe_err(f"Error creating file {target}: {e}")
        sys.exit(1)

    print(Fore.GREEN + f"Created: {target}" + Fore.RESET)
    if print_only:
        print(str(target))
        return target

    editor_parts = _select_editor(cfg, open_with, verbose)
    if editor_parts:
        try:
            subprocess.Popen([*editor_parts, str(target)], shell=False)
            if verbose: print(f"Opened file with: {' '.join(editor_parts)}")
        except Exception as e:
            print(Fore.RED + f"Open failed: {e}" + Fore.RESET)
    else:
        if os.name == "nt":
            try:
                os.startfile(str(target))  # type: ignore[attr-defined]
                if verbose: print(f"Opened file with default Windows association: {target}")
            except Exception:
                if verbose: print("No editor found; Windows fallback failed.")
    return target

def show_tree(path, depth=2):
    root = Path(path)
    if not root.exists():
        _safe_err(f"Missing: {root}")
        sys.exit(1)
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if len(rel.parts) > depth:
            continue
        indent = "  " * (len(rel.parts) - 1)
        print(f"{indent}{p.name}{'/' if p.is_dir() else ''}")

def merge_templates_from_json(templates, json_path: str, overwrite: bool, verbose=False):
    p = Path(json_path).expanduser()
    if not p.exists():
        _safe_err(f"Templates file not found: {p}")
        sys.exit(2)
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            _safe_err("Templates JSON must be an object mapping extensions to template strings or objects.")
            sys.exit(2)
        updated = 0
        for k, v in data.items():
            ext = norm_ext(k)
            if not ext: 
                if verbose: _safe_err(f"Skipping invalid template key: {k}")
                continue
            lst = _normalize_template_value(v)
            if not overwrite and ext.lower() in templates:
                if verbose: print(f"Skipping existing templates for {ext}")
                continue
            templates[ext.lower()] = lst
            updated += len(lst)
            if verbose: print(f"Added/updated {len(lst)} template(s) for {ext}")
        if verbose: print(f"Merged {updated} template variants from {p}")
    except json.JSONDecodeError as e:
        _safe_err(f"Invalid JSON in {p}: {e}")
        sys.exit(2)
    except Exception as e:
        _safe_err(f"Failed to read templates JSON: {e}")
        sys.exit(2)

def merge_templates_from_dir(templates, dir_path: str, overwrite: bool, verbose=False):
    d = Path(dir_path).expanduser()
    if not d.is_dir():
        _safe_err(f"Template directory not found: {d}")
        sys.exit(2)
    added = 0
    for f in sorted(d.iterdir()):
        if not f.is_file(): 
            continue
        ext = _ext_from_dir_entry(f.name)
        if not ext: 
            continue
        try:
            body = f.read_text(encoding="utf-8")
        except Exception as e:
            _safe_err(f"Failed to read {f}: {e}")
            sys.exit(2)
        item = {"desc": f.name, "body": body}
        if overwrite or ext.lower() not in templates:
            templates[ext.lower()] = [item]
            added += 1
            if verbose: print(f"Added template for {ext} from {f.name}")
        else:
            # append to existing list
            lst = _normalize_template_value(templates[ext.lower()])
            lst.append(item)
            templates[ext.lower()] = lst
            added += 1
            if verbose: print(f"Appended template for {ext} from {f.name}")
    if verbose: print(f"Loaded {added} template file(s) from {d}")

def main():
    cfg = load_cfg()
    templates = load_templates()

    ap = argparse.ArgumentParser(prog="newfile", description="Quick file/project helper.")
    ap.add_argument("file", nargs="?", help="Optional name (e.g. 'jimbob' or 'src/jimbob.py').")

    # create flags
    ap.add_argument("-n", "--name", help="Base filename (no extension).")
    ap.add_argument("-t", "--type", help="File extension (e.g. .py). Use 'off' to require manual.")
    ap.add_argument("--dir", help="Subdirectory under project.")
    ap.add_argument("--openwith", help="Program to open new file with (overrides config).")
    ap.add_argument("--template", help="Use template: '.ext', '.ext#N', '.ext@desc', or 'fromfile:PATH'.")
    ap.add_argument("--print", action="store_true", help="Print created path and exit with 0.")
    ap.add_argument("--force", action="store_true", help="Overwrite existing files without prompting.")
    ap.add_argument("--dry-run", action="store_true", help="Simulate file creation (no I/O).")
    ap.add_argument("--verbose", action="store_true", help="Print detailed processing information.")
    # description for settemplate
    ap.add_argument("--desc", help="Description for --settemplate (optional).")

    # admin/config group (mutually exclusive)
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--setpro", metavar="PATH", help="Set project folder.")
    grp.add_argument("--settype", metavar="EXT_OR_off", help="Set default file extension or 'off'.")
    grp.add_argument("--asktype", choices=["on", "off"], help="Toggle ask-for-type.")
    grp.add_argument("--show", action="store_true", help="Show config + templates file path.")
    grp.add_argument("--tree", nargs="?", const="2", metavar="DEPTH", help="Show project tree (default depth 2).")
    grp.add_argument("--seteditor", metavar="PROG", help="Set default editor (e.g. code, notepad, pycharm).")
    grp.add_argument("--settemplate", nargs=2, metavar=("EXT", "CONTENT"), help="Set template for extension. Use fromfile:PATH to load external file.")
    grp.add_argument("--settemplates-json", metavar="JSON_PATH", help="Merge templates from JSON file (object {'.ext': 'content'|'list'|'object', ...}).")
    grp.add_argument("--settemplates-dir", metavar="DIR_PATH", help="Bulk load templates from directory (file name == extension).")
    grp.add_argument("--listtemplates", action="store_true", help="List available templates (with descriptions).")

    # overwrite flag OUTSIDE of the group (so it can be combined with settemplates-*) 
    ap.add_argument("--overwrite-templates", action="store_true", help="When merging/bulk-loading templates, overwrite existing entries.")

    args = ap.parse_args()

    # template ops
    if args.settemplate:
        ext, content = args.settemplate
        ext = norm_ext(ext)
        if not ext:
            _safe_err("Invalid extension for template.")
            sys.exit(1)
        if content.lower().startswith("fromfile:"):
            path = content.split(":", 1)[1].strip().strip('"').strip("'")
            p = Path(path).expanduser()
            if not p.exists():
                _safe_err(f"Template file not found: {p}"); sys.exit(2)
            try:
                content = p.read_text(encoding="utf-8")
                if args.verbose: print(f"Loaded template content from {p}")
            except Exception as e:
                _safe_err(f"Failed to read template file '{p}': {e}"); sys.exit(2)
        item = {"desc": (args.desc or "").strip(), "body": content}
        lst = templates.get(ext.lower(), [])
        lst = _normalize_template_value(lst)
        lst.append(item)
        templates[ext.lower()] = lst
        save_templates(templates)
        print(Fore.GREEN + f"Template added for {ext}." + Fore.RESET)
        return

    if args.settemplates_json:
        merge_templates_from_json(templates, args.settemplates_json, overwrite=args.overwrite_templates, verbose=args.verbose)
        save_templates(templates)
        print(Fore.GREEN + f"Merged templates from {args.settemplates_json}; saved to {CFG_TEMPLATES}." + Fore.RESET)
        return

    if args.settemplates_dir:
        merge_templates_from_dir(templates, args.settemplates_dir, overwrite=args.overwrite_templates, verbose=args.verbose)
        save_templates(templates)
        print(Fore.GREEN + f"Loaded templates from {args.settemplates_dir}; saved to {CFG_TEMPLATES}." + Fore.RESET)
        return

    if args.listtemplates:
        if not templates:
            print("(no templates)")
        else:
            for ext in sorted(templates.keys()):
                items = _normalize_template_value(templates[ext])
                if not items: 
                    print(ext)
                    continue
                print(f"{ext}:")
                for i, t in enumerate(items, 1):
                    desc = t.get("desc","") or "(no description)"
                    print(f"  {i}. {desc}")
        return

    # config ops
    if args.seteditor:
        val = args.seteditor.strip().strip('"').strip("'")
        cfg["editor"] = val
        save_cfg(cfg)
        print(Fore.GREEN + f"Editor set: {val}" + Fore.RESET)
        return

    if args.setpro:
        cfg["project"] = str(Path(args.setpro).expanduser())
        save_cfg(cfg)
        print(Fore.GREEN + f"Project set: {cfg['project']}" + Fore.RESET)
        return

    if args.settype:
        if args.settype.lower() == "off":
            cfg["default_ext"] = ""
            cfg["ask_type"] = True
        else:
            cfg["default_ext"] = norm_ext(args.settype)
            cfg["ask_type"] = False
        save_cfg(cfg)
        print(Fore.GREEN + f"default_ext={cfg.get('default_ext') or 'OFF'} ask_type={cfg.get('ask_type')}" + Fore.RESET)
        return

    if args.asktype:
        cfg["ask_type"] = (args.asktype == "on")
        save_cfg(cfg)
        print(Fore.GREEN + f"ask_type={cfg['ask_type']}" + Fore.RESET)
        return

    if args.show:
        info = {
            "config_path": str(CFG_PATH),
            "templates_path": str(CFG_TEMPLATES),
            **cfg
        }
        print(json.dumps(info, indent=2))
        return

    if args.tree is not None:
        try: depth = int(args.tree)
        except Exception: depth = 2
        show_tree(cfg["project"], depth=depth)
        return

    # default action: create
    name, ext, subdir = args.name, args.type, args.dir
    if args.file:
        fp = Path(args.file)
        if fp.suffix and not ext: ext = fp.suffix
        if not name: name = fp.stem if fp.suffix else fp.name
        if fp.parent and str(fp.parent) != "." and not subdir: subdir = str(fp.parent)

    create_file(cfg, templates, name=name, ext=ext, subdir=subdir,
                open_with=args.openwith, template=args.template,
                print_only=args.print, force=args.force, dry_run=args.dry_run,
                verbose=args.verbose)
    sys.exit(0)

if __name__ == "__main__":
    main()
