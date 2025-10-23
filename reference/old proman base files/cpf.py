# Meta-data for usage in PowerShell/CMD

import os
import zipfile
from pathlib import Path
from datetime import datetime
import argparse
import json
import re
import uuid
import sys

# Script version for flag metadata
SCRIPT_VERSION = "2.5"  # [FIX] Updated for --soft-recursive ZIP fix

# Maximum number of files to process
MAX_FILES = 20000

# Default max file size (10MB) if not specified
DEFAULT_MAX_SIZE = 10 * 1024 * 1024

# Define default filetype groups
FILETYPE_GROUPS = {
    'python': ['.py', '.pyc', '.ipynb', '.txt', '.json'],
    'web': ['.html', '.asp', '.php', '.css', '.js', '.json', '.txt'],
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
    'all': None,
    'list': []
}

# Define text file extensions for content inclusion
TEXT_EXTENSIONS = ['.py', '.txt', '.json', '.html', '.asp', '.php', '.css', '.js']

def should_list_only_dir(path, base, list_only_dirs):
    try:
        rel_parts = Path(path).relative_to(base).parts
        return any(part in list_only_dirs for part in rel_parts)
    except Exception:
        return False

def load_custom_filetype_groups(config_path="filetypes.json"):
    """Load custom filetype groups from a JSON file, if it exists."""
    try:
        if Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_groups = json.load(f)
            FILETYPE_GROUPS.update({k.lower(): v for k, v in custom_groups.items()})
    except Exception as e:
        print(f"[!] Error loading custom filetypes from {config_path}: {e}")

def parse_size(size_str):
    """Parse size string (e.g., '5MB', '1024KB') to bytes."""
    units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3}
    match = re.match(r'(\d+\.?\d*)\s*(KB|MB|GB)', size_str, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid size format: {size_str}. Use e.g., '5MB' or '1024KB'.")
    value, unit = float(match.group(1)), match.group(2).upper()
    return int(value * units[unit])

def is_cpf_zip(full_path, verbose=False, cache=None):
    """Check if a ZIP file is a CPF-generated archive."""
    if cache is not None and str(full_path) in cache:
        if verbose:
            print(f"[!] Cache hit for CPF archive (zip): {full_path}")
        return cache[str(full_path)]
    
    try:
        with zipfile.ZipFile(full_path, 'r') as zf:
            is_cpf = 'cpf_archive_flag.txt' in zf.namelist()
            if is_cpf and verbose:
                print(f"[!] Identified CPF archive (zip): {full_path}")
            if cache is not None:
                cache[str(full_path)] = is_cpf
            return is_cpf
    except (zipfile.BadZipFile, Exception) as e:
        if verbose:
            print(f"[!] Error checking ZIP {full_path}: {e}")
        if cache is not None:
            cache[str(full_path)] = False
        return False

def is_cpf_txt(full_path, verbose=False, cache=None):
    """Check if a TXT file is a CPF-generated archive."""
    if cache is not None and str(full_path) in cache:
        if verbose:
            print(f"[!] Cache hit for CPF archive (txt): {full_path}")
        return cache[str(full_path)]
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            is_cpf = first_line.startswith("CPF Archive Flag:")
            if is_cpf and verbose:
                print(f"[!] Identified CPF archive (txt): {full_path}")
            if cache is not None:
                cache[str(full_path)] = is_cpf
            return is_cpf
    except Exception as e:
        if verbose:
            print(f"[!] Error checking TXT {full_path}: {e}")
        if cache is not None:
            cache[str(full_path)] = False
        return False

def create_flag_content(timestamp):
    """Generate content for the CPF archive flag."""
    flag_id = str(uuid.uuid4())
    return f"""CPF Archive Flag:
Script: cpf.py
Version: {SCRIPT_VERSION}
Timestamp: {timestamp}
Flag-ID: {flag_id}
"""

def create_psr_log(output_base, timestamp, args, directories, processed_files, skipped_subdir_files, errors, interrupted=False, current_file=None, total_files=0, verbose=False):
    """Generate a PSR-style log file summarizing execution."""
    psr_file = Path(output_base) / f"cpf_psr_log_{timestamp}.txt"
    command = " ".join(sys.argv)
    flag_content = create_flag_content(timestamp)

    with open(psr_file, 'w', encoding='utf-8') as psrf:
        psrf.write(flag_content)
        psrf.write("\n")
        psrf.write("CPF Problem Steps Recorder Log\n")
        psrf.write("=" * 50 + "\n")
        psrf.write(f"Timestamp: {timestamp}\n")
        psrf.write(f"Command: {command}\n")
        psrf.write(f"Output File: {Path(output_base) / f'project_output_{timestamp}.{args.format}'}\n")
        psrf.write(f"Status: {'Interrupted' if interrupted else 'Completed'}\n")
        psrf.write(f"Total Files Processed: {len(processed_files)}\n")
        psrf.write(f"Estimated Total Files in Directory: {total_files}\n")
        if interrupted and current_file:
            psrf.write(f"Interrupted While Processing: {current_file}\n")
        psrf.write(f"Arguments:\n")
        for arg, value in vars(args).items():
            psrf.write(f"  {arg}: {value}\n")
        psrf.write("\nDirectories Processed:\n")
        for dir_path in directories:
            psrf.write(f"  {dir_path}\n")
        psrf.write("\nFiles Processed:\n")
        for file_path in processed_files:
            psrf.write(f"  {file_path}\n")
        if not processed_files:
            psrf.write("  None\n")
        psrf.write("\nSubdirectory Files Skipped (soft-recursive):\n")
        for file_path in skipped_subdir_files:
            psrf.write(f"  {file_path}\n")
        if not skipped_subdir_files:
            psrf.write("  None\n")
        psrf.write("\nErrors/Warnings:\n")
        for error in errors:
            psrf.write(f"  {error}\n")
        if not errors:
            psrf.write("  None\n")
        psrf.write("=" * 50 + "\n")
    
    if verbose:
        print(f"[+] PSR log saved to: {psr_file}")
    return psr_file

def count_files(directories, verbose=False):
    """Estimate total files in directories."""
    total = 0
    for directory in directories:
        try:
            for root, _, files in os.walk(Path(directory)):
                total += len(files)
        except Exception as e:
            if verbose:
                print(f"[!] Error counting files in {directory}: {e}")
    return total

def zip_project(directories, output_base, output_format="zip", recursive=True, soft_recursive=False, filetypes="web", custom_filetypes=None, exclude=None, verbose=False, max_size=None, depth=None, only_list=False, summary=False, include_cpf_archives=False, list_only_dirs=None):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    output_file = Path(output_base) / f"project_output_{timestamp}.{output_format}"
    psr_file_pattern = f"cpf_psr_log_{timestamp}"

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Estimate total files
    total_files = count_files(directories, verbose)
    if verbose:
        print(f"[+] Starting CPF in {', '.join(directories)}")
        print(f"[+] Output directory: {output_base}")
        print(f"[+] Estimated total files: {total_files}")

    # Initialize output_dir_name
    output_dir_name = None
    output_base_resolved = output_file.parent.resolve()
    for dir_path in directories:
        try:
            if output_base_resolved.is_relative_to(Path(dir_path).resolve()):
                output_dir_name = output_base_resolved.name
                print(f"[!] Warning: Output directory {output_base} is within input directory {dir_path}. Use --output-dir to avoid issues.")
                if verbose:
                    print(f"[+] Set output_dir_name to {output_dir_name} for exclusion")
                break
        except Exception as e:
            if verbose:
                print(f"[!] Error checking directory overlap for {dir_path}: {e}")
            continue

    # Determine allowed and excluded extensions
    if filetypes == 'list' and custom_filetypes:
        allowed_extensions = [f".{ext.lower().lstrip('.')} " for ext in custom_filetypes.split(",")]
    else:
        allowed_extensions = FILETYPE_GROUPS.get(filetypes.lower(), None)
    exclude_extensions = [f".{ext.lower().lstrip('.')} " for ext in exclude.split(",")] if exclude else []

    # Parse max_size or use default
    max_size_bytes = parse_size(max_size) if max_size else DEFAULT_MAX_SIZE

    # Initialize tracking for PSR log
    processed_files = []
    skipped_subdir_files = []  # [NEW] Track subdirectory files for PSR log
    errors = []
    summary_count = 0
    flag_cache = {}
    interrupted = False
    current_file = None
    script_path = Path(__file__).resolve()

    try:
        if output_format == "zip":
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                flag_content = create_flag_content(timestamp)
                zipf.writestr('cpf_archive_flag.txt', flag_content)
                if verbose:
                    print("[+] Added CPF archive flag to zip")

                for directory in directories:
                    base = Path(directory)
                    if not base.exists():
                        error_msg = f"[!] Skipped missing directory: {directory}"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    for root, dirs, files in os.walk(base):
                        if output_dir_name is not None and Path(root).name == output_dir_name:
                            dirs[:] = []
                            if verbose:
                                print(f"[+] Skipped output directory: {root}")
                            continue
                        if depth is not None:
                            depth_level = len(Path(root).relative_to(base).parts)
                            if depth_level > depth:
                                dirs[:] = []
                                continue
                        # [FIX] Handle soft-recursive and list-only-dirs for ZIP
                        if (soft_recursive and Path(root) != base) or should_list_only_dir(root, base, list_only_dirs):
                            # List subdirectory files but dont zip
                            for file in files:
                                full_path = Path(root) / file
                                try:
                                    rel_path = full_path.relative_to(base.parent)
                                    skipped_subdir_files.append(str(rel_path))
                                    if verbose:
                                        print(f"[+] Skipped zipping (soft-recursive): {rel_path}")
                                except Exception as e:
                                    errors.append(f"[!] Error listing{full_path}: {e}")
                            continue  # Skip zipping files in subdirectories
                        if not recursive and not soft_recursive and Path(root) != base:
                            continue
                        if '__pycache__' in root:
                            continue

                        for file in files:
                            if summary_count >= MAX_FILES:
                                error_msg = f"[!] Maximum file limit ({MAX_FILES}) reached; stopping processing."
                                print(error_msg)
                                errors.append(error_msg)
                                return

                            full_path = Path(root) / file
                            if full_path.resolve() == script_path:
                                if verbose:
                                    print(f"[!] Skipped script itself: {full_path}")
                                continue
                            current_file = str(full_path)
                            if (full_path == output_file or
                                full_path.name.startswith(psr_file_pattern) or
                                full_path.name.startswith("project_output_")):
                                if verbose:
                                    print(f"[!] Skipped output file: {full_path}")
                                continue
                            if not include_cpf_archives and full_path.name.startswith("project_output_"):
                                if file.lower().endswith('.zip') and is_cpf_zip(full_path, verbose, flag_cache):
                                    continue
                                if file.lower().endswith('.txt') and is_cpf_txt(full_path, verbose, flag_cache):
                                    continue
                            if any(file.lower().endswith(ext) for ext in exclude_extensions):
                                continue
                            if allowed_extensions and not any(file.lower().endswith(ext) for ext in allowed_extensions):
                                continue
                            file_size = full_path.stat().st_size
                            if file_size > max_size_bytes:
                                error_msg = f"[!] Skipped {full_path}: Exceeds max size {max_size_bytes/(1024*1024):.2f}MB"
                                if verbose:
                                    print(error_msg)
                                errors.append(error_msg)
                                continue
                            try:
                                rel_path = full_path.relative_to(base.parent)
                                zipf.write(full_path, arcname=rel_path)
                                summary_count += 1
                                processed_files.append(str(rel_path))
                                if verbose and summary_count % 10 == 0:
                                    print(f"[+] Processed {summary_count} files")
                                if verbose:
                                    print(f"[+] Added to zip: {rel_path}")
                            except Exception as e:
                                error_msg = f"[!] Error zipping {full_path}: {e}"
                                print(error_msg)
                                errors.append(error_msg)
            print(f"[+] Project zipped to: {output_file}")
            if summary:
                print(f"[+] Total files zipped: {summary_count}")

        elif output_format == "txt":
            with open(output_file, 'w', encoding='utf-8') as txtf:
                flag_content = create_flag_content(timestamp)
                txtf.write(flag_content)
                txtf.write("\n")
                txtf.write("Project Files Listing\n")
                txtf.write(f"Generated: {timestamp}\n")
                txtf.write(f"Filetypes: {filetypes}{' (' + custom_filetypes + ')' if filetypes == 'list' else ''}\n")
                txtf.write(f"Excluded: {exclude if exclude else 'None'}\n")
                txtf.write(f"Max Size: {max_size_bytes/(1024*1024):.2f}MB\n")
                txtf.write("=" * 50 + "\n\n")
                
                for directory in directories:
                    base = Path(directory)
                    if not base.exists():
                        error_msg = f"[!] Missing directory: {directory}"
                        txtf.write(error_msg + "\n")
                        errors.append(error_msg)
                        continue

                    txtf.write(f"Directory: {base.name}\n")
                    for root, dirs, files in os.walk(base):
                        if output_dir_name is not None and Path(root).name == output_dir_name:
                            dirs[:] = []
                            if verbose:
                                print(f"[+] Skipped output directory: {root}")
                            continue
                        if depth is not None:
                            depth_level = len(Path(root).relative_to(base).parts)
                            if depth_level > depth:
                                dirs[:] = []
                                continue
                        if not recursive and not soft_recursive and Path(root) != base:
                            continue
                        if '__pycache__' in root:
                            continue

                        if recursive or soft_recursive:
                            for subdir in dirs:
                                txtf.write(f"Subdirectory: {subdir}/\n")

                        for file in files:
                            if summary_count >= MAX_FILES:
                                error_msg = f"[!] Maximum file limit ({MAX_FILES}) reached; stopping processing."
                                txtf.write(error_msg + "\n")
                                errors.append(error_msg)
                                return

                            full_path = Path(root) / file
                            if full_path.resolve() == script_path:
                                if verbose:
                                    print(f"[!] Skipped script itself: {full_path}")
                                continue
                            current_file = str(full_path)
                            if (full_path == output_file or
                                full_path.name.startswith(psr_file_pattern) or
                                full_path.name.startswith("project_output_")):
                                if verbose:
                                    print(f"[!] Skipped output file: {full_path}")
                                continue
                            if not include_cpf_archives and full_path.name.startswith("project_output_"):
                                if file.lower().endswith('.zip') and is_cpf_zip(full_path, verbose, flag_cache):
                                    continue
                                if file.lower().endswith('.txt') and is_cpf_txt(full_path, verbose, flag_cache):
                                    continue
                            if any(file.lower().endswith(ext) for ext in exclude_extensions):
                                continue
                            if allowed_extensions and not any(file.lower().endswith(ext) for ext in allowed_extensions):
                                continue
                            file_size = full_path.stat().st_size
                            if file_size > max_size_bytes:
                                error_msg = f"[!] Skipped {full_path}: Exceeds max size {max_size_bytes/(1024*1024):.2f}MB"
                                if verbose:
                                    print(error_msg)
                                errors.append(error_msg)
                                continue
                            try:
                                rel_path = full_path.relative_to(base.parent)
                                txtf.write(f"File: {rel_path}\n")
                                if (soft_recursive and Path(root) != base) or should_list_only_dir(root, base, list_only_dirs):
                                    skipped_subdir_files.append(str(rel_path))  # [NEW]
                                    if verbose:
                                        print(f"[+] Listed: {rel_path} (no contents, soft-recursive)")
                                else:
                                    summary_count += 1
                                    processed_files.append(str(rel_path))
                                    if verbose and summary_count % 10 == 0:
                                        print(f"[+] Processed {summary_count} files")
                                    if verbose:
                                        print(f"[+] Listed: {rel_path}")
                                
                                include_contents = not only_list and full_path.suffix.lower() in TEXT_EXTENSIONS and full_path.stat().st_size < 1024 * 1024 and not should_list_only_dir(root, base, list_only_dirs)
                                if (soft_recursive and Path(root) != base) or should_list_only_dir(root, base, list_only_dirs):
                                    include_contents = False
                                if include_contents:
                                    try:
                                        with open(full_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                        txtf.write("Contents:\n")
                                        txtf.write(content + "\n")
                                        txtf.write("-" * 50 + "\n")
                                    except Exception as e:
                                        error_msg = f"Error reading file {rel_path}: {e}"
                                        txtf.write(error_msg + "\n")
                                        errors.append(error_msg)
                            except Exception as e:
                                error_msg = f"Error processing file {full_path}: {e}"
                                txtf.write(error_msg + "\n")
                                errors.append(error_msg)
                    if summary:
                        txtf.write(f"Total files listed in {base.name}: {summary_count}\n")
                    txtf.write("\n")
            print(f"[+] Project listing saved to: {output_file}")

    except KeyboardInterrupt:
        interrupted = True
        print("[!] Process interrupted by user.")
        errors.append(f"Process interrupted by user while processing: {current_file}")
        raise
    finally:
        create_psr_log(output_base, timestamp, args, directories, processed_files, skipped_subdir_files, errors, interrupted, current_file, total_files, verbose)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CopyProjectFiles: Zip or create a text file of project directories and files.")
    parser.add_argument("--dir", type=str, help="Directory to process (default: current directory)")
    parser.add_argument("--format", type=str, choices=["zip", "txt"], default="zip", help="Output format: 'zip' or 'txt' (default: zip)")
    
    recursive_group = parser.add_mutually_exclusive_group()
    recursive_group.add_argument("--no-recursive", action="store_false", dest="recursive", help="Disable recursive processing of subdirectories")
    recursive_group.add_argument("--soft-recursive", action="store_true", help="Process base directory fully; list only folder/file names for subdirectories")
    
    parser.add_argument("--filetypes", type=str, choices=list(FILETYPE_GROUPS.keys()), default="web",
                        help="Filetype group to include: 'python', 'web', 'image', 'all', or 'list' (requires --extensions; default: web)")
    parser.add_argument("--extensions", type=str, help="Comma-separated file extensions for 'list' (e.g., 'py,txt')")
    parser.add_argument("--exclude", type=str, help="Comma-separated file extensions to exclude (e.g., 'pyc,bak')")
    parser.add_argument("--verbose", action="store_true", help="Print detailed processing information")
    parser.add_argument("--output-dir", type=str, help="Directory for output file (default: current directory)")
    parser.add_argument("--max-size", type=str, help="Max file size (e.g., '5MB', '1024KB'; default: 10MB)")
    parser.add_argument("--list-only-dirs", type=str, help="Comma-separated subdir names to treat as list-only")
    parser.add_argument("--depth", type=int, default=None, help="Max directory depth to recurse (default: unlimited)")
    parser.add_argument("--only-list", action="store_true", help="List file paths only, skip reading file contents")
    parser.add_argument("--summary", action="store_true", help="Show counts per directory summary at end")
    parser.add_argument("--include-cpf-archives", action="store_true", help="Include previous CPF-generated archives (default: excluded)")
    args = parser.parse_args()
    
    if args.filetypes == 'list' and not args.extensions:
        parser.error("--extensions is required when --filetypes=list")

    load_custom_filetype_groups()
    parser._actions[3].choices = list(FILETYPE_GROUPS.keys())

    script_dir = Path.cwd()
    output_base = Path(args.output_dir) if args.output_dir else script_dir
    dirs_to_process = [args.dir] if args.dir else [str(script_dir)]

    
    list_only_dirs = args.list_only_dirs.split(',') if args.list_only_dirs else []
    zip_project(
        dirs_to_process,
        output_base,
        args.format,
        args.recursive if 'recursive' in args else True,
        args.soft_recursive,
        args.filetypes,
        args.extensions,
        args.exclude,
        args.verbose,
        args.max_size,
        args.depth,
        args.only_list,
        args.summary,
        args.include_cpf_archives,
        list_only_dirs
    )