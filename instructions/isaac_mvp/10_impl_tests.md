# Implementation: Tests (Tier Validator)

## Goal
Create pytest tests for tier_validator.py (safety-critical module).

**Time Estimate:** 15 minutes

**Dependencies:** 06_impl_core_logic.md (tier_validator.py must exist)

---

## File 1: conftest.py

**Path:** `tests/conftest.py`

**Purpose:** Shared pytest fixtures for all tests.

**Complete Implementation:**

```python
"""
Pytest configuration and shared fixtures.
"""

import pytest
from pathlib import Path
from isaac.models.preferences import Preferences


@pytest.fixture
def default_preferences():
    """Create default Preferences instance for testing."""
    return Preferences(
        machine_id='TEST-MACHINE',
        auto_run_tier2=False,
        tier_overrides={},
        api_url='',
        api_key=''
    )


@pytest.fixture
def custom_preferences():
    """Create Preferences with custom tier overrides."""
    return Preferences(
        machine_id='TEST-MACHINE',
        auto_run_tier2=True,
        tier_overrides={
            'find': 1,      # Override find to Tier 1
            'grep': 1,      # Override grep to Tier 1
            'rm': 3         # Override rm to Tier 3 (safer)
        },
        api_url='',
        api_key=''
    )


@pytest.fixture
def tier_defaults():
    """Load tier_defaults.json for verification."""
    import json
    from pathlib import Path
    
    data_dir = Path(__file__).parent.parent / 'isaac' / 'data'
    tier_file = data_dir / 'tier_defaults.json'
    
    with open(tier_file, 'r') as f:
        return json.load(f)
```

---

## File 2: pytest.ini

**Path:** `tests/pytest.ini`

**Purpose:** Pytest configuration.

**Complete Implementation:**

```ini
[pytest]
# Test discovery patterns
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Output verbosity
addopts = -v --tb=short

# Test paths
testpaths = tests

# Coverage (optional)
# addopts = -v --tb=short --cov=isaac --cov-report=html

# Warnings
filterwarnings =
    ignore::DeprecationWarning
```

---

## File 3: test_tier_validator.py

**Path:** `tests/test_tier_validator.py`

**Purpose:** Comprehensive tests for tier validation (safety-critical).

**Complete Implementation:**

```python
"""
Tests for tier_validator.py
SAFETY-CRITICAL: 100% coverage required.
"""

import pytest
from isaac.core.tier_validator import TierValidator


class TestTier1Commands:
    """Test Tier 1 (instant execution) classification."""
    
    def test_ls_command(self, default_preferences):
        """ls should be Tier 1 (instant)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('ls') == 1
    
    def test_cd_command(self, default_preferences):
        """cd should be Tier 1 (instant)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('cd /tmp') == 1
    
    def test_pwd_command(self, default_preferences):
        """pwd should be Tier 1 (instant)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('pwd') == 1
    
    def test_powershell_get_childitem(self, default_preferences):
        """Get-ChildItem (PowerShell) should be Tier 1."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('Get-ChildItem') == 1


class TestTier3Commands:
    """Test Tier 3 (validation required) classification."""
    
    def test_git_command(self, default_preferences):
        """git should be Tier 3."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('git status') == 3
    
    def test_cp_command(self, default_preferences):
        """cp should be Tier 3."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('cp file1 file2') == 3
    
    def test_mv_command(self, default_preferences):
        """mv should be Tier 3."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('mv old new') == 3


class TestTier4Commands:
    """
    Test Tier 4 (destructive/lockdown) classification.
    CRITICAL SAFETY TEST - Must prevent accidental data loss.
    """
    
    def test_rm_rf_bash(self, default_preferences):
        """rm -rf should be Tier 4 (CRITICAL for bash)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('rm -rf /') == 4
    
    def test_rm_command(self, default_preferences):
        """rm should be Tier 4."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('rm file') == 4
    
    def test_format_command(self, default_preferences):
        """format should be Tier 4."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('format C:') == 4
    
    def test_powershell_remove_item(self, default_preferences):
        """Remove-Item (PowerShell) should be Tier 4 (CRITICAL for Windows)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('Remove-Item -Recurse') == 4


class TestCustomOverrides:
    """Test custom tier overrides from preferences."""
    
    def test_override_find_to_tier1(self, custom_preferences):
        """find should be Tier 1 when overridden."""
        validator = TierValidator(custom_preferences)
        assert validator.get_tier('find /') == 1
    
    def test_override_grep_to_tier1(self, custom_preferences):
        """grep should be Tier 1 when overridden."""
        validator = TierValidator(custom_preferences)
        assert validator.get_tier('grep pattern') == 1
    
    def test_override_rm_to_tier3(self, custom_preferences):
        """rm should be Tier 3 when overridden (safer)."""
        validator = TierValidator(custom_preferences)
        assert validator.get_tier('rm file') == 3
    
    def test_override_takes_precedence(self, custom_preferences, tier_defaults):
        """Custom overrides should take precedence over defaults."""
        validator = TierValidator(custom_preferences)
        
        # find is normally Tier 2.5, should be 1 with override
        assert validator.get_tier('find') == 1
        assert 'find' in tier_defaults['2.5']  # Verify it's in defaults


class TestUnknownCommands:
    """Test handling of unknown commands."""
    
    def test_unknown_command_defaults_tier3(self, default_preferences):
        """Unknown commands should default to Tier 3 (safe)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('unknown_command_xyz') == 3
    
    def test_empty_command_defaults_tier3(self, default_preferences):
        """Empty command should default to Tier 3."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('') == 3
    
    def test_whitespace_command_defaults_tier3(self, default_preferences):
        """Whitespace-only command should default to Tier 3."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('   ') == 3


class TestCrossPlatform:
    """Test both PowerShell and bash commands."""
    
    def test_powershell_and_bash_ls(self, default_preferences):
        """Both ls (bash) and Get-ChildItem (PS) should be Tier 1."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('ls') == 1
        assert validator.get_tier('Get-ChildItem') == 1
    
    def test_powershell_and_bash_destructive(self, default_preferences):
        """Both rm (bash) and Remove-Item (PS) should be Tier 4."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('rm') == 4
        assert validator.get_tier('Remove-Item') == 4


class TestEdgeCases:
    """Test edge cases and potential issues."""
    
    def test_command_with_args(self, default_preferences):
        """Tier should be determined by command name, not args."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('ls -la /tmp') == 1
        assert validator.get_tier('rm -rf /tmp') == 4
    
    def test_command_with_pipes(self, default_preferences):
        """First command determines tier (pipes not parsed)."""
        validator = TierValidator(default_preferences)
        assert validator.get_tier('ls | grep test') == 1
    
    def test_case_sensitive(self, default_preferences):
        """Command matching should be case-sensitive."""
        validator = TierValidator(default_preferences)
        # ls (lowercase) is defined
        assert validator.get_tier('ls') == 1
        # LS (uppercase) is NOT defined, should default to 3
        assert validator.get_tier('LS') == 3


class TestTierDefaults:
    """Verify tier_defaults.json structure."""
    
    def test_tier_defaults_loaded(self, default_preferences, tier_defaults):
        """Tier defaults should load from file."""
        validator = TierValidator(default_preferences)
        assert validator.defaults == tier_defaults
    
    def test_all_tiers_present(self, tier_defaults):
        """All 5 tiers should be present in defaults."""
        assert '1' in tier_defaults
        assert '2' in tier_defaults
        assert '2.5' in tier_defaults
        assert '3' in tier_defaults
        assert '4' in tier_defaults
    
    def test_tier1_has_commands(self, tier_defaults):
        """Tier 1 should have at least 5 commands."""
        assert len(tier_defaults['1']) >= 5
    
    def test_tier4_has_destructive(self, tier_defaults):
        """Tier 4 should include rm and format."""
        tier4_commands = tier_defaults['4']
        assert 'rm' in tier4_commands or 'Remove-Item' in tier4_commands
        assert 'format' in tier4_commands or 'Format-Volume' in tier4_commands


class TestPerformance:
    """Test performance of tier classification."""
    
    def test_lookup_speed(self, default_preferences):
        """1000 lookups should complete in <100ms."""
        import time
        validator = TierValidator(default_preferences)
        
        start = time.time()
        for _ in range(1000):
            validator.get_tier('ls')
        elapsed = time.time() - start
        
        assert elapsed < 0.1  # Should be < 100ms


# Test summary
def test_coverage_summary(default_preferences):
    """Summary test to ensure critical scenarios are covered."""
    validator = TierValidator(default_preferences)
    
    # Critical safety checks
    assert validator.get_tier('rm -rf /') == 4  # Prevent data loss
    assert validator.get_tier('format C:') == 4  # Prevent disk wipe
    
    # Safe commands execute instantly
    assert validator.get_tier('ls') == 1
    assert validator.get_tier('pwd') == 1
    
    # Unknown defaults to safe
    assert validator.get_tier('unknown') == 3
```

---

## Running Tests

### Install pytest (if not already)
```bash
pip install pytest
```

### Run all tests
```bash
pytest tests/
```

**Expected output:**
```
============================= test session starts ==============================
collected 30 items

tests/test_tier_validator.py::TestTier1Commands::test_ls_command PASSED
tests/test_tier_validator.py::TestTier1Commands::test_cd_command PASSED
...
tests/test_tier_validator.py::test_coverage_summary PASSED

============================== 30 passed in 0.15s ===============================
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run specific test class
```bash
pytest tests/test_tier_validator.py::TestTier4Commands -v
```

### Run with coverage (optional)
```bash
pip install pytest-cov
pytest tests/ --cov=isaac.core.tier_validator --cov-report=html
```

---

## Verification Steps

### 1. Check Test Files Exist
```bash
ls tests/
```

**Expected:**
```
conftest.py
pytest.ini
test_tier_validator.py
```

### 2. Run Tests
```bash
pytest tests/
```

**Expected:** All 30+ tests pass

### 3. Check Critical Tests Pass
```bash
pytest tests/test_tier_validator.py::TestTier4Commands -v
```

**Expected:** All Tier 4 tests pass (CRITICAL for safety)

---

## Common Pitfalls

⚠️ **Import errors**
- **Symptom:** `ModuleNotFoundError: No module named 'isaac'`
- **Fix:** Run `pip install -e .` from project root

⚠️ **tier_defaults.json not found**
- **Symptom:** Tests fail with FileNotFoundError
- **Fix:** Ensure tier_defaults.json exists in isaac/data/

⚠️ **Tests fail on Windows/Linux differences**
- **Symptom:** Some tests pass on one platform, fail on other
- **Fix:** Use platform-specific fixtures

⚠️ **Performance test fails**
- **Symptom:** `test_lookup_speed` fails on slow machine
- **Fix:** Increase threshold from 0.1s to 0.5s

---

## Success Signals

✅ All 3 test files created  
✅ pytest discovers tests (30+ tests found)  
✅ All Tier 1 tests pass  
✅ All Tier 3 tests pass  
✅ **All Tier 4 tests pass (CRITICAL for safety)**  
✅ Custom override tests pass  
✅ Unknown command tests pass  
✅ Cross-platform tests pass  
✅ Edge case tests pass  
✅ Performance test passes  
✅ 100% of tests passing  
✅ Ready for next step (Deployment Guide)

---

**Next Step:** 11_deployment.md (Full deployment guide for user)

---

**END OF TESTS IMPLEMENTATION**
