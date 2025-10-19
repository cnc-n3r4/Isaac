# Implementation: Project Bootstrap

## Goal
Create project structure, setup.py, and requirements.txt for Isaac 2.0 MVP.

**Time Estimate:** 15 minutes

---

## Step 1: Create Directory Structure

Create these directories:

```
isaac/
├── isaac/
│   ├── core/
│   ├── adapters/
│   ├── api/
│   ├── ui/
│   ├── models/
│   ├── utils/
│   └── data/
├── php_api/
├── tests/
└── docs/
```

**Commands:**
```bash
mkdir -p isaac/core isaac/adapters isaac/api isaac/ui isaac/models isaac/utils isaac/data
mkdir -p php_api tests docs
```

---

## Step 2: Create __init__.py Files

Every Python package needs `__init__.py`:

```bash
touch isaac/__init__.py
touch isaac/core/__init__.py
touch isaac/adapters/__init__.py
touch isaac/api/__init__.py
touch isaac/ui/__init__.py
touch isaac/models/__init__.py
touch isaac/utils/__init__.py
```

**Contents for all __init__.py files:**
```python
# Isaac 2.0 - Multi-platform shell assistant
```

---

## Step 3: Create setup.py

**File:** `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name='isaac',
    version='2.0.0',
    description='Multi-platform intelligent shell assistant with cloud sync',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.31.0',
        'colorama>=0.4.6',
        'prompt-toolkit>=3.0.43',
    ],
    entry_points={
        'console_scripts': [
            'isaac=isaac.__main__:main',
        ],
    },
    package_data={
        'isaac': ['data/*.json', 'data/*.txt'],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
```

---

## Step 4: Create requirements.txt

**File:** `requirements.txt`

```
requests==2.31.0
colorama==0.4.6
prompt-toolkit==3.0.43
pytest==7.4.3
```

**Why these packages:**
- `requests` - Cloud sync HTTP calls to GoDaddy PHP API
- `colorama` - ANSI color support (especially for Windows)
- `prompt-toolkit` - Advanced input handling (future: arrow key history)
- `pytest` - Testing framework

---

## Step 5: Create .gitignore

**File:** `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/

# Isaac specific
.isaac/
*.jsonl
```

---

## Step 6: Create README.md (Basic)

**File:** `README.md`

```markdown
# Isaac 2.0 - Multi-Platform Shell Assistant

Intelligent shell wrapper with cloud-synced sessions and 5-tier command validation.

## Features
- Multi-platform (PowerShell + bash)
- Cloud session roaming across machines
- 5-tier command safety system
- Splash screen + locked header UI
- Natural language queries (Phase 2)

## Installation

```bash
pip install -e .
```

## Usage

```bash
isaac --start
```

## Requirements
- Python 3.8+
- Windows (PowerShell 7+ or 5.1) OR Linux (bash)
- GoDaddy hosting (for cloud sync)

## Project Structure
```
isaac/
├── core/          # Session management, command routing, tier validation
├── adapters/      # Shell abstraction (PowerShell, bash)
├── api/           # Cloud sync client
├── ui/            # Terminal control, splash, header, prompt
├── models/        # Data structures (preferences, command history)
├── utils/         # Config loader, logging, validators
└── data/          # Static data (tier defaults, splash art)
```

## Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest tests/

# Launch Isaac
isaac --start
```

## License
MIT
```

---

## Verification Steps

After completing this implementation:

### 1. Check Directory Structure
```bash
ls -R isaac/
```

**Expected output:**
```
isaac/:
core/ adapters/ api/ ui/ models/ utils/ data/ __init__.py

isaac/core:
__init__.py

isaac/adapters:
__init__.py

... (etc for all subdirectories)
```

### 2. Verify setup.py
```bash
python setup.py --version
```

**Expected:** `2.0.0`

### 3. Test Installation (Will fail until code exists, but checks setup.py)
```bash
pip install -e .
```

**Expected:** Package installs, creates `isaac.egg-info/`

### 4. Verify Entry Point (Will fail until __main__.py exists)
```bash
isaac --help
```

**Expected (after __main__.py created):** Help text

---

## Common Pitfalls

⚠️ **Missing __init__.py**
- **Symptom:** `ModuleNotFoundError: No module named 'isaac.core'`
- **Fix:** Create `__init__.py` in every package directory

⚠️ **Wrong Python version**
- **Symptom:** `pip install` fails with syntax errors
- **Fix:** Use Python 3.8+, check with `python --version`

⚠️ **Package data not included**
- **Symptom:** `tier_defaults.json` not found at runtime
- **Fix:** Ensure `include_package_data=True` and `package_data` in setup.py

⚠️ **Entry point not working**
- **Symptom:** `isaac` command not found after install
- **Fix:** Reinstall with `pip install -e .` after creating `__main__.py`

---

## Success Signals

✅ Directory structure created  
✅ All `__init__.py` files present  
✅ `setup.py` validates (python setup.py --version)  
✅ `pip install -e .` succeeds  
✅ `isaac.egg-info/` directory created  
✅ Ready for next step (data files)

---

**Next Step:** 03_impl_data_files.md (Create tier_defaults.json, splash_art.txt)

---

**END OF BOOTSTRAP IMPLEMENTATION**
