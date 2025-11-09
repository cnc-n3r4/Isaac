# PHASE 2: QUALITY - IMPLEMENTATION KICKOFF

**Agent Role:** Phase 2 Quality Engineer
**Prerequisites:** Phase 1 COMPLETE (application functional & secure)
**Timeline:** Week 3-4 (1.5 weeks / 120 hours)
**Goal:** Build quality foundation - make it maintainable and reliable
**Branch:** `claude/phase-2-quality-[your-session-id]`

---

## 🎯 YOUR MISSION

Transform ISAAC from **functional & secure** (6.5/10) to **maintainable & tested** (8.0/10) by:
- Adding 70% test coverage
- Refactoring complex code
- Standardizing command implementations
- Cleaning up technical debt

---

## ✅ PREREQUISITES CHECK

Before starting Phase 2, verify Phase 1 completion:

```bash
# 1. Application starts
python -c "import isaac.core.command_router"

# 2. Dependencies installed
python -c "import jsonschema, dotenv, flask, anthropic, openai"

# 3. Alias system integrated
grep -r "UnixAliasTranslator" isaac/core/command_router.py

# 4. No shell=True usage
grep -r "shell=True" isaac/ | wc -l  # Should be 0 or minimal

# 5. Tier 4 commands added
python -c "import json; data=json.load(open('isaac/data/tier_defaults.json')); print(len(data['tier4']))"  # Should be 39+
```

**If any checks fail, complete Phase 1 first!**

---

## 📋 TASK LIST (Execute in Order)

### WEEK 3: Testing & Refactoring

#### Task 2.1: Set Up Quality Tools (4 hours)

**Install tools:**
```bash
pip install pytest pytest-cov pytest-mock
pip install black isort flake8 mypy
pip install autoflake radon
pip install pre-commit
```

**Run baseline measurements:**
```bash
# Test coverage
pytest tests/ --cov=isaac --cov-report=html
# Opens in browser: htmlcov/index.html

# Code complexity
radon cc isaac/ -a -nb > baseline_complexity.txt

# Type hints
mypy isaac/ --strict > baseline_types.txt 2>&1

# PEP 8 compliance
flake8 isaac/ --max-line-length=100 > baseline_pep8.txt 2>&1
```

**Save baseline report:** `quality_baseline_report.md`

**Success:** All tools installed, baseline metrics documented

---

#### Task 2.2: Remove Technical Debt (8 hours)

**2.2.1: Remove Unused Imports (2 hours)**
```bash
# Dry run first
autoflake --remove-all-unused-imports --recursive --dry-run isaac/

# If looks good, apply
autoflake --remove-all-unused-imports --recursive --in-place isaac/

# Commit
git add isaac/
git commit -m "refactor: Remove 70+ unused imports"
```

**2.2.2: Fix PEP 8 Violations (2 hours)**
```bash
# Format code
black isaac/ --line-length 100

# Sort imports
isort isaac/ --profile black

# Verify
flake8 isaac/ --max-line-length=100

# Commit
git add isaac/
git commit -m "style: Format code with black and isort (PEP 8 compliance)"
```

**2.2.3: Add Type Hints to Core Modules (4 hours)**

Focus on these 5 critical files:
1. `isaac/core/command_router.py`
2. `isaac/core/session_manager.py`
3. `isaac/ai/router.py`
4. `isaac/core/tier_validator.py`
5. `isaac/core/boot_loader.py`

**Example:**
```python
# Before
def route_command(self, command_str, context):
    pass

# After
from typing import Dict, Any
from isaac.models import CommandResult

def route_command(self, command_str: str, context: Dict[str, Any]) -> CommandResult:
    pass
```

**Tool-assisted:**
```bash
pip install monkeytype
monkeytype run python -m isaac
monkeytype apply isaac.core.command_router
```

**Commit after each file:**
```bash
git add isaac/core/command_router.py
git commit -m "refactor: Add type hints to command_router"
```

**Success:** Type hints coverage improves from 62% to 80%+

---

#### Task 2.3: Refactor Command Router (16 hours)

**Goal:** Reduce cyclomatic complexity from 34 to <10

**2.3.1: Create Base Strategy Class (2 hours)**

**Create:** `isaac/core/routing/strategy.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class CommandStrategy(ABC):
    """Base class for command routing strategies"""

    @abstractmethod
    def can_handle(self, cmd: str) -> bool:
        """Check if this strategy can handle the command"""
        pass

    @abstractmethod
    def execute(self, cmd: str, context: Dict[str, Any]) -> CommandResult:
        """Execute the command"""
        pass

    @abstractmethod
    def get_help(self) -> str:
        """Get help text for this command"""
        pass
```

**2.3.2: Extract Command Handlers (8 hours)**

Create strategy files for major commands:

**Example:** `isaac/core/routing/read_strategy.py`
```python
from isaac.core.routing.strategy import CommandStrategy
from isaac.models import CommandResult

class ReadCommandStrategy(CommandStrategy):
    def can_handle(self, cmd: str) -> bool:
        return cmd.strip().startswith('/read') or cmd.strip().startswith('read ')

    def execute(self, cmd: str, context: Dict[str, Any]) -> CommandResult:
        # All read logic here
        file_path = self._parse_file_path(cmd)
        content = self._read_file(file_path)
        return CommandResult(success=True, content=content)

    def get_help(self) -> str:
        return "Read a file: /read <file_path>"

    def _parse_file_path(self, cmd: str) -> str:
        # Helper method
        pass

    def _read_file(self, path: str) -> str:
        # Helper method
        pass
```

**Create strategies for:**
- ReadCommandStrategy
- WriteCommandStrategy
- EditCommandStrategy
- GrepCommandStrategy
- GlobCommandStrategy
- HelpCommandStrategy
- StatusCommandStrategy
- ConfigCommandStrategy
- AskCommandStrategy
- AnalyzeCommandStrategy
- (10-15 strategies total)

**2.3.3: Update Router to Use Strategies (2 hours)**

**Modify:** `isaac/core/command_router.py`
```python
from isaac.core.routing.strategy import CommandStrategy
from isaac.core.routing.read_strategy import ReadCommandStrategy
from isaac.core.routing.write_strategy import WriteCommandStrategy
# ... import all strategies

class CommandRouter:
    def __init__(self):
        self.strategies: List[CommandStrategy] = [
            ReadCommandStrategy(),
            WriteCommandStrategy(),
            EditCommandStrategy(),
            GrepCommandStrategy(),
            GlobCommandStrategy(),
            # ... register all strategies
        ]

    def route_command(self, cmd_str: str, context: Dict[str, Any]) -> CommandResult:
        # Apply alias translation (from Phase 1)
        cmd_str = self._apply_alias_translation(cmd_str, context)

        # Try each strategy
        for strategy in self.strategies:
            if strategy.can_handle(cmd_str):
                return strategy.execute(cmd_str, context)

        raise UnknownCommandError(f"Unknown command: {cmd_str}")
```

**2.3.4: Write Strategy Tests (3 hours)**

**Create:** `tests/test_routing_strategies.py`
```python
import pytest
from isaac.core.routing.read_strategy import ReadCommandStrategy

def test_read_strategy_can_handle():
    strategy = ReadCommandStrategy()
    assert strategy.can_handle('/read test.txt')
    assert strategy.can_handle('read test.txt')
    assert not strategy.can_handle('/write test.txt')

def test_read_strategy_execute():
    strategy = ReadCommandStrategy()
    result = strategy.execute('/read test.txt', {})
    assert result.success == True
    # ... more assertions
```

**2.3.5: Integration Testing (1 hour)**

Verify complexity reduction:
```bash
radon cc isaac/core/command_router.py -nb
# Should show complexity <10
```

**Commit:**
```bash
git add isaac/core/routing/ isaac/core/command_router.py tests/
git commit -m "refactor: Extract command router to strategy pattern (complexity 34→5)"
```

**Success:** Command router complexity <10, individually testable strategies

---

#### Task 2.4: Implement Core Module Tests (32 hours)

**Goal:** Achieve 70% test coverage on core modules

**2.4.1: CommandRouter Tests (8 hours)**

**Create:** `tests/core/test_command_router.py`
```python
import pytest
from isaac.core.command_router import CommandRouter
from isaac.models import CommandResult

class TestCommandRouter:
    @pytest.fixture
    def router(self):
        return CommandRouter()

    def test_route_read_command(self, router):
        result = router.route_command('/read test.txt', {})
        assert result.success == True
        assert result.command_type == 'read'

    def test_route_write_command(self, router):
        result = router.route_command('/write test.txt "content"', {})
        assert result.success == True
        assert result.command_type == 'write'

    def test_route_dangerous_command_requires_tier4(self, router):
        result = router.route_command('sudo rm -rf /', {})
        assert result.tier == 4
        assert result.requires_confirmation == True

    def test_alias_translation_windows(self, router, monkeypatch):
        monkeypatch.setattr('platform.system', lambda: 'Windows')
        result = router.route_command('ls -la', {})
        assert 'Get-ChildItem' in result.translated_command

    def test_unknown_command_raises_error(self, router):
        with pytest.raises(UnknownCommandError):
            router.route_command('/nonexistent', {})

    # ... 15+ more tests
```

**2.4.2: TierValidator Tests (6 hours)**

**Create:** `tests/core/test_tier_validator.py`
```python
import pytest
from isaac.core.tier_validator import TierValidator

class TestTierValidator:
    @pytest.fixture
    def validator(self):
        return TierValidator()

    def test_tier4_commands_blocked(self, validator):
        assert validator.validate('sudo rm -rf /') == 4
        assert validator.validate('docker rm -f container') == 4
        assert validator.validate('git push --force') == 4

    def test_tier3_requires_ai(self, validator):
        result = validator.validate('some unusual command')
        assert result.tier == 3
        assert result.requires_ai_validation == True

    def test_tier1_instant_execution(self, validator):
        assert validator.validate('/help') == 1
        assert validator.validate('/status') == 1

    def test_force_flag_still_requires_tier4(self, validator):
        result = validator.validate('sudo rm -rf / /force')
        assert result.tier == 4
        assert result.force_flag_ignored == True

    # ... 10+ more tests
```

**2.4.3: AI Router Tests (8 hours)**

**Create:** `tests/ai/test_router.py`
```python
import pytest
from unittest.mock import Mock, patch
from isaac.ai.router import AIRouter

class TestAIRouter:
    @pytest.fixture
    def router(self):
        return AIRouter()

    def test_provider_fallback_on_failure(self, router):
        # Mock primary provider failure
        with patch('isaac.ai.providers.openai_provider.query', side_effect=Exception):
            result = router.query("test prompt")
            # Should fallback to Claude or Grok
            assert result.success == True
            assert result.provider != 'openai'

    def test_cost_optimization_selects_cheapest(self, router):
        result = router.query("simple task", optimize_cost=True)
        # Should select cheaper model for simple task
        assert result.model in ['gpt-3.5-turbo', 'claude-haiku']

    def test_streaming_mode(self, router):
        responses = list(router.query_stream("test prompt"))
        assert len(responses) > 0
        assert all(isinstance(r, str) for r in responses)

    def test_timeout_handling(self, router):
        with patch('isaac.ai.providers.openai_provider.query', side_effect=TimeoutError):
            result = router.query("test", timeout=1)
            assert result.success == False
            assert result.error_type == 'timeout'

    # ... 15+ more tests
```

**2.4.4: SessionManager Tests (6 hours)**

**Create:** `tests/core/test_session_manager.py`
```python
import pytest
from isaac.core.session_manager import SessionManager

class TestSessionManager:
    @pytest.fixture
    def manager(self):
        return SessionManager()

    def test_session_creation(self, manager):
        session = manager.create_session('test_user')
        assert session.id is not None
        assert session.user == 'test_user'

    def test_session_persistence(self, manager):
        session = manager.create_session('test_user')
        session.set_state('key', 'value')
        manager.save_session(session)

        # Reload
        loaded = manager.load_session(session.id)
        assert loaded.get_state('key') == 'value'

    def test_session_cleanup(self, manager):
        old_session = manager.create_session('test', created_days_ago=31)
        manager.cleanup_old_sessions(days=30)
        assert manager.get_session(old_session.id) is None

    # ... 10+ more tests
```

**2.4.5: CostOptimizer Tests (4 hours)**

**Create:** `tests/ai/test_cost_optimizer.py`
```python
import pytest
from isaac.ai.cost_optimizer import CostOptimizer

class TestCostOptimizer:
    @pytest.fixture
    def optimizer(self):
        return CostOptimizer()

    def test_model_selection_for_simple_task(self, optimizer):
        model = optimizer.select_model("what is 2+2?", complexity='low')
        assert model in ['gpt-3.5-turbo', 'claude-haiku']

    def test_model_selection_for_complex_task(self, optimizer):
        model = optimizer.select_model("complex coding task", complexity='high')
        assert model in ['gpt-4', 'claude-opus']

    def test_cost_tracking(self, optimizer):
        optimizer.log_query('gpt-4', tokens=1000)
        cost = optimizer.get_total_cost()
        assert cost > 0

    # ... 8+ more tests
```

**Run all tests:**
```bash
pytest tests/ --cov=isaac --cov-report=html --cov-report=term
# Target: 70% coverage
```

**Commit:**
```bash
git add tests/
git commit -m "test: Add comprehensive test suite (70% coverage achieved)"
```

**Success:** Test coverage 15% → 70%+

---

### WEEK 4: Polish & Documentation

#### Task 2.5: Command Schema Standardization (16 hours)

**2.5.1: Create Standard Base Classes (4 hours)**

**Create:** `isaac/commands/base.py`
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CommandManifest:
    name: str
    description: str
    usage: str
    examples: List[str]
    tier: int

class BaseCommand(ABC):
    @abstractmethod
    def execute(self, args: List[str], flags: Dict[str, Any]) -> CommandResult:
        """Execute the command"""
        pass

    @abstractmethod
    def get_manifest(self) -> CommandManifest:
        """Get command metadata"""
        pass

    def get_help(self) -> str:
        """Generate help text from manifest"""
        manifest = self.get_manifest()
        return f"""
{manifest.name} - {manifest.description}

Usage: {manifest.usage}

Examples:
{chr(10).join(f"  {ex}" for ex in manifest.examples)}

Safety Tier: {manifest.tier}
"""

class FlagParser:
    """Unified flag parsing for all commands"""
    def __init__(self, args: List[str]):
        self.args = args
        self.flags = {}
        self.positional = []
        self._parse()

    def _parse(self):
        # Standard flag parsing logic
        pass

    def get_flag(self, name: str, default=None):
        return self.flags.get(name, default)

    def get_positional(self, index: int, default=None):
        return self.positional[index] if index < len(self.positional) else default

class CommandResponse:
    """Standard response format"""
    def __init__(self, success: bool, data: Any = None, error: str = None):
        self.success = success
        self.data = data
        self.error = error

    def to_dict(self):
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error
        }
```

**2.5.2: Refactor Commands to Use Base (8 hours)**

Update top 10-15 most-used commands:

**Example:** `isaac/commands/read/command.py`
```python
from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse

class ReadCommand(BaseCommand):
    def execute(self, args: List[str], flags: Dict[str, Any]) -> CommandResponse:
        parser = FlagParser(args)
        file_path = parser.get_positional(0)

        if not file_path:
            return CommandResponse(False, error="File path required")

        try:
            with open(file_path, 'r') as f:
                content = f.read()
            return CommandResponse(True, data=content)
        except Exception as e:
            return CommandResponse(False, error=str(e))

    def get_manifest(self) -> CommandManifest:
        return CommandManifest(
            name="read",
            description="Read contents of a file",
            usage="/read <file_path> [--lines N]",
            examples=[
                "/read config.json",
                "/read log.txt --lines 50",
                "/read README.md"
            ],
            tier=1
        )
```

**Commands to update:**
1. read
2. write
3. edit
4. grep
5. glob
6. ask
7. analyze
8. status
9. config
10. help

**2.5.3: Create Command Template (2 hours)**

**Create:** `isaac/commands/TEMPLATE.py`
```python
"""
Command Template - Copy this to create new commands
"""
from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from typing import List, Dict, Any

class YourCommand(BaseCommand):
    def execute(self, args: List[str], flags: Dict[str, Any]) -> CommandResponse:
        parser = FlagParser(args)

        # Parse arguments
        arg1 = parser.get_positional(0)
        flag1 = parser.get_flag('flag-name', default=False)

        # Validate
        if not arg1:
            return CommandResponse(False, error="Argument required")

        # Execute
        try:
            result = self._do_work(arg1, flag1)
            return CommandResponse(True, data=result)
        except Exception as e:
            return CommandResponse(False, error=str(e))

    def get_manifest(self) -> CommandManifest:
        return CommandManifest(
            name="yourcommand",
            description="Brief description",
            usage="/yourcommand <arg> [--flag]",
            examples=[
                "/yourcommand example1",
                "/yourcommand example2 --flag"
            ],
            tier=2  # 1-4
        )

    def _do_work(self, arg, flag):
        # Implementation
        pass
```

**2.5.4: Write Migration Guide (2 hours)**

**Create:** `docs/COMMAND_MIGRATION_GUIDE.md`

**Commit:**
```bash
git add isaac/commands/base.py isaac/commands/*/command.py docs/COMMAND_MIGRATION_GUIDE.md
git commit -m "refactor: Standardize command schema (30/42 commands)"
```

**Success:** 30/42 commands standardized (71%)

---

#### Task 2.6: Add Caching Layer (12 hours)

**2.6.1: Implement Alias Cache (4 hours)**

**Create:** `isaac/crossplatform/alias_cache.py`
```python
import json
import time
import os
from typing import Dict, Optional

class AliasCache:
    def __init__(self, cache_file: str = 'aliases.json', ttl: int = 300):
        self.cache_file = cache_file
        self.ttl = ttl  # 5 minutes
        self._cache: Optional[Dict] = None
        self._last_load: float = 0
        self._file_mtime: float = 0

    def get_aliases(self) -> Dict:
        current_mtime = os.path.getmtime(self.cache_file)
        current_time = time.time()

        # Reload if file changed or cache expired
        if (self._cache is None or
            current_mtime > self._file_mtime or
            current_time - self._last_load > self.ttl):

            with open(self.cache_file) as f:
                self._cache = json.load(f)
            self._file_mtime = current_mtime
            self._last_load = current_time

        return self._cache

    def invalidate(self):
        """Manually invalidate cache"""
        self._cache = None
```

**Update translator to use cache:**
```python
# isaac/crossplatform/unix_alias_translator.py
from isaac.crossplatform.alias_cache import AliasCache

class UnixAliasTranslator:
    def __init__(self):
        self.cache = AliasCache()

    def translate(self, cmd: str, target: str = 'powershell') -> str:
        aliases = self.cache.get_aliases()  # Fast cached access
        return aliases.get(cmd, cmd)
```

**2.6.2: Implement Query Cache (4 hours)**

**Create:** `isaac/ai/query_cache.py`
```python
from functools import lru_cache
import hashlib
import json
import os
from typing import Optional

class QueryCache:
    def __init__(self, cache_dir: str = '.isaac_cache', max_memory: int = 1000):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self._memory_cache = {}  # LRU cache in memory

    def _generate_key(self, query: str, model: str) -> str:
        content = f"{query}:{model}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, query: str, model: str) -> Optional[str]:
        key = self._generate_key(query, model)

        # Check memory cache
        if key in self._memory_cache:
            return self._memory_cache[key]

        # Check disk cache
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(cache_file):
            with open(cache_file) as f:
                data = json.load(f)
                response = data['response']
                self._memory_cache[key] = response  # Promote to memory
                return response

        return None

    def set(self, query: str, model: str, response: str):
        key = self._generate_key(query, model)

        # Store in memory
        self._memory_cache[key] = response

        # Store on disk
        cache_file = os.path.join(self.cache_dir, f"{key}.json")
        with open(cache_file, 'w') as f:
            json.dump({'query': query, 'model': model, 'response': response}, f)

    def clear(self):
        """Clear all caches"""
        self._memory_cache.clear()
        for file in os.listdir(self.cache_dir):
            os.remove(os.path.join(self.cache_dir, file))
```

**Update AI router:**
```python
# isaac/ai/router.py
from isaac.ai.query_cache import QueryCache

class AIRouter:
    def __init__(self):
        self.cache = QueryCache()

    def query(self, prompt: str, model: str = 'gpt-4') -> str:
        # Check cache first
        cached = self.cache.get(prompt, model)
        if cached:
            return cached

        # Query AI provider
        response = self._query_provider(prompt, model)

        # Cache response
        self.cache.set(prompt, model, response)

        return response
```

**2.6.3: Test Caching (2 hours)**

**Create:** `tests/test_caching.py`
```python
import pytest
from isaac.crossplatform.alias_cache import AliasCache
from isaac.ai.query_cache import QueryCache

def test_alias_cache_hit():
    cache = AliasCache()
    aliases1 = cache.get_aliases()
    aliases2 = cache.get_aliases()
    assert aliases1 is aliases2  # Same object = cache hit

def test_query_cache_hit():
    cache = QueryCache()
    cache.set("test query", "gpt-4", "test response")
    result = cache.get("test query", "gpt-4")
    assert result == "test response"

# ... more tests
```

**2.6.4: Add Cache Management Commands (2 hours)**

**Create:** `isaac/commands/cache/command.py`
```python
class CacheCommand(BaseCommand):
    def execute(self, args: List[str], flags: Dict[str, Any]) -> CommandResponse:
        action = args[0] if args else 'status'

        if action == 'status':
            return self._show_status()
        elif action == 'clear':
            return self._clear_caches()
        elif action == 'warmup':
            return self._warmup_caches()

    def _show_status(self):
        # Show cache hit rates, sizes, etc.
        pass

    def _clear_caches(self):
        # Clear all caches
        pass
```

**Commit:**
```bash
git add isaac/crossplatform/alias_cache.py isaac/ai/query_cache.py tests/test_caching.py
git commit -m "feat: Add caching layer (alias 50-100x faster, query cache saves costs)"
```

**Success:** Alias lookups <1ms, query cache working

---

#### Task 2.7: Documentation Consolidation (20 hours)

**2.7.1: Create New Structure (2 hours)**

```bash
mkdir -p docs/{architecture,guides,reference,project}

# Move and organize
mv ALIAS_SYSTEM_ANALYSIS.md docs/architecture/
mv SECURITY_ANALYSIS.md docs/architecture/
mv PERFORMANCE_ANALYSIS.md docs/architecture/
mv PLUGIN_ARCHITECTURE_ANALYSIS.md docs/architecture/

mv ALIAS_QUICK_REFERENCE.md docs/guides/
mv PLUGIN_SYSTEM_QUICK_REFERENCE.md docs/guides/

mv ISAAC_COMMAND_REFERENCE.md docs/reference/
mv COMPLETE_REFERENCE.md docs/reference/

# Archive obsolete
mkdir -p docs/archive
mv PHASE_3_COMPLETE.md docs/archive/
mv CLEANUP_SUMMARY.md docs/archive/
mv SETUP_COMPLETE.md docs/archive/
```

**2.7.2: Consolidate Documentation (12 hours)**

Merge and update key documents (detailed work - follow IMPLEMENTATION_ROADMAP.md Task 2.7 for full details)

**2.7.3: Fix Markdown Formatting (2 hours)**

```bash
npm install -g markdownlint-cli
markdownlint --fix docs/**/*.md *.md
```

**2.7.4: Create Documentation Index (2 hours)**

**Update:** `docs/README.md`

**2.7.5: Cross-link Documents (2 hours)**

Add navigation links between related docs

**Commit:**
```bash
git add docs/ *.md
git commit -m "docs: Consolidate and organize documentation (41→20 files)"
```

**Success:** Clean docs structure, no duplicates

---

#### Task 2.8: Performance Quick Wins (8 hours)

(See QUICK_WINS.md Task 10 for details)

- Lists → Sets for O(1) lookups (2 hours)
- Dict dispatch instead of if/elif (2 hours)
- Pre-compile regex patterns (2 hours)
- Benchmark improvements (2 hours)

**Success:** 30-40% performance improvement

---

#### Task 2.9: CI/CD Setup (8 hours)

**2.9.1: Create GitHub Actions Workflows (4 hours)**

**Create:** `.github/workflows/test.yml`
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov=isaac --cov-report=term
      - name: Check coverage
        run: |
          coverage report --fail-under=70
```

**Create:** `.github/workflows/lint.yml`
**Create:** `.github/workflows/security.yml`

**2.9.2: Setup Pre-commit Hooks (2 hours)**

**Create:** `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/PyCQA/isort
    rev: 5.12.0
    hooks:
      - id: isort
  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

Install:
```bash
pre-commit install
```

**2.9.3: Configure Code Quality Tools (2 hours)**

Setup CodeClimate, SonarQube, or similar

**Commit:**
```bash
git add .github/workflows/ .pre-commit-config.yaml
git commit -m "ci: Add CI/CD pipelines and pre-commit hooks"
```

**Success:** Automated testing on every commit

---

#### Task 2.10: Phase 2 Completion Report (4 hours)

**Create:** `PHASE_2_COMPLETION_REPORT.md`

Document:
- Quality metrics comparison
- Test coverage improvement (15% → 70%+)
- Complexity reduction (34 → <10)
- Performance benchmarks (+30-40%)
- Documentation status
- Technical debt removed
- Phase 3 readiness

---

## ✅ SUCCESS CRITERIA

Phase 2 complete when:

- [x] Test coverage ≥70% (core modules)
- [x] Command router complexity <10
- [x] Type hints ≥80% (core modules)
- [x] PEP 8 compliance ≥98%
- [x] 30/42 commands standardized
- [x] Caching layer implemented (+30-50% faster)
- [x] Documentation organized (20 clean files)
- [x] CI/CD pipelines running
- [x] All tests pass
- [x] No unused imports
- [x] Pre-commit hooks working

---

## 📊 EXPECTED IMPROVEMENTS

| Metric | Before (Phase 1) | After (Phase 2) | Improvement |
|--------|------------------|-----------------|-------------|
| **Overall Health** | 6.5/10 | 8.0/10 | +23% |
| Test Coverage | 20% | 70% | +250% |
| Code Complexity | 34 max | <10 max | -71% |
| Type Hints | 62% | 80% | +29% |
| PEP 8 Compliance | 94% | 98% | +4% |
| Performance | Baseline | +30-40% | +35% avg |
| Documentation | 6.2/10 | 8.5/10 | +37% |

---

## 🧪 PHASE 2 TEST SUITE

Run comprehensive tests:
```bash
# All tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=isaac --cov-report=html
# Opens htmlcov/index.html

# Specific modules
pytest tests/core/ -v
pytest tests/ai/ -v
pytest tests/commands/ -v

# Performance benchmarks
pytest tests/benchmarks/ -v
```

---

## 📝 COMMIT STRATEGY

Commit after each major task completion:
- Technical debt removal
- Refactoring
- Test suites
- Documentation
- CI/CD setup

Use descriptive commit messages with conventional commits format:
- `test: Add comprehensive test suite for core modules`
- `refactor: Extract command router to strategy pattern`
- `docs: Consolidate and organize documentation`
- `ci: Add GitHub Actions workflows`

---

## 📚 REFERENCE DOCUMENTS

- **IMPLEMENTATION_ROADMAP.md** - Phase 2 full details
- **QUICK_WINS.md** - P1 tasks for quick improvements
- **EXECUTIVE_SUMMARY.md** - Strategic context
- **MASTER_CHECKLIST.md** - Overall progress tracking

---

## 🚧 IF YOU GET STUCK

**Test failures:**
- Check dependencies installed: `pip list`
- Clear pytest cache: `pytest --cache-clear`
- Run specific test: `pytest tests/test_file.py::test_name -v`

**Refactoring issues:**
- Make small changes incrementally
- Test after each change
- Keep old code commented until new code works
- Use git branches for risky refactors

**Coverage not improving:**
- Focus on core modules first
- Test public methods, not private internals
- Use mocks for external dependencies
- Check coverage report: `coverage html`

---

## ⏭️ NEXT PHASE

After Phase 2 completion:
- **Phase 3 (Optimization)** - See PHASE_3_KICKOFF.md
- Focus: Async AI, parallel loading, advanced caching
- Goal: 5-10x overall performance improvement

---

**READY TO BUILD QUALITY!** 🏗️

Start with Task 2.1 (Set Up Quality Tools).
