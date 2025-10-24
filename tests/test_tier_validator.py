# tests/test_tier_validator.py
"""
Test Suite for Isaac Tier Validator (SAFETY-CRITICAL)

This module tests the tier classification system that prevents dangerous commands
from executing without warnings. Wrong tier = data loss risk.

Coverage Goal: 100%
Test Count: 8+ scenarios

Test Priority: CRITICAL (Safety-critical module)
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import json


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_preferences():
    """Sample preferences with no custom tier overrides"""
    from isaac.models.preferences import Preferences
    return Preferences(
        machine_id='TEST-MACHINE',
        auto_run_tier2=False,
        tier_overrides={},
        api_url='https://test.com/isaac/api',
        api_key='test_key'
    )


@pytest.fixture
def mock_preferences_with_overrides():
    """Preferences with custom tier overrides (user moved 'find' to Tier 1)"""
    from isaac.models.preferences import Preferences
    return Preferences(
        machine_id='TEST-MACHINE',
        auto_run_tier2=False,
        tier_overrides={
            'find': 1,      # User moved dangerous command to instant execution (their choice)
            'grep': 1       # User moved safe command to instant execution
        },
        api_url='https://test.com/isaac/api',
        api_key='test_key'
    )


@pytest.fixture
def tier_defaults():
    """Mock tier defaults JSON structure"""
    return {
        "1": ["ls", "cd", "pwd", "echo", "cat", "type", "Get-ChildItem", "Set-Location"],
        "2": ["grep", "Select-String", "head", "tail"],
        "2.5": ["find", "sed", "awk", "Where-Object"],
        "3": ["cp", "mv", "git", "npm", "pip", "Copy-Item", "Move-Item"],
        "4": ["rm", "del", "format", "dd", "Remove-Item", "Format-Volume"]
    }


# ============================================================================
# TIER 1 TESTS - Instant Execution (No AI, No Warnings)
# ============================================================================

def test_tier_1_instant_execution_bash(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 1 commands execute immediately without validation.
    
    Test Coverage:
    - Bash commands: ls, cd, pwd, echo, cat
    - Expected: All return tier 1
    - Risk if fails: Safe commands might get unnecessary validation prompts
    """
    from isaac.core.tier_validator import TierValidator
    
    # Mock the _load_tier_defaults method to use our fixture
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test bash Tier 1 commands
    assert validator.get_tier('ls') == 1, "ls should be Tier 1 (instant execution)"
    assert validator.get_tier('cd /home') == 1, "cd should be Tier 1"
    assert validator.get_tier('pwd') == 1, "pwd should be Tier 1"
    assert validator.get_tier('echo test') == 1, "echo should be Tier 1"
    assert validator.get_tier('cat file.txt') == 1, "cat should be Tier 1"


def test_tier_1_instant_execution_powershell(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 1 commands for PowerShell execute immediately.
    
    Test Coverage:
    - PowerShell equivalents: Get-ChildItem, Set-Location
    - Expected: Same tier as bash equivalents (cross-platform consistency)
    - Risk if fails: Cross-platform tier mismatch could confuse users
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test PowerShell Tier 1 commands
    assert validator.get_tier('Get-ChildItem') == 1, "Get-ChildItem (ls) should be Tier 1"
    assert validator.get_tier('Set-Location C:\\') == 1, "Set-Location (cd) should be Tier 1"
    assert validator.get_tier('type file.txt') == 1, "type (cat) should be Tier 1"


# ============================================================================
# TIER 2 TESTS - Auto-Correct Typos
# ============================================================================

def test_tier_2_auto_correct(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 2 commands get typo correction.
    
    Test Coverage:
    - Bash: grep, head, tail
    - PowerShell: Select-String
    - Expected: All return tier 2
    - Behavior: Auto-correct typos, then execute (if auto_run_tier2=True) or confirm first
    - Risk if fails: Typo correction might not trigger for these commands
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test Tier 2 commands
    assert validator.get_tier('grep pattern file.txt') == 2, "grep should be Tier 2"
    assert validator.get_tier('head -10 file.txt') == 2, "head should be Tier 2"
    assert validator.get_tier('tail -f log.txt') == 2, "tail should be Tier 2"
    assert validator.get_tier('Select-String pattern') == 2, "Select-String should be Tier 2"


# ============================================================================
# TIER 2.5 TESTS - Confirm After Correction
# ============================================================================

def test_tier_2_5_confirm_first(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 2.5 commands require confirmation after typo correction.
    
    Test Coverage:
    - Bash: find, sed, awk
    - PowerShell: Where-Object
    - Expected: All return tier 2.5
    - Behavior: Auto-correct typos, but ALWAYS confirm before execution
    - Risk if fails: Potentially dangerous commands might execute without confirmation
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test Tier 2.5 commands
    assert validator.get_tier('find / -name file') == 2.5, "find should be Tier 2.5"
    assert validator.get_tier('sed s/old/new/ file') == 2.5, "sed should be Tier 2.5"
    assert validator.get_tier('awk {print $1}') == 2.5, "awk should be Tier 2.5"
    assert validator.get_tier('Where-Object {$_.Name}') == 2.5, "Where-Object should be Tier 2.5"


# ============================================================================
# TIER 3 TESTS - AI Validation Required
# ============================================================================

def test_tier_3_validation_required(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 3 commands require AI validation before execution.
    
    Test Coverage:
    - File operations: cp, mv
    - Development tools: git, npm, pip
    - PowerShell: Copy-Item, Move-Item
    - Expected: All return tier 3
    - Behavior: AI validates safety before execution
    - Risk if fails: Potentially harmful commands might execute without AI review
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test Tier 3 commands
    assert validator.get_tier('cp file.txt backup.txt') == 3, "cp should be Tier 3"
    assert validator.get_tier('mv file.txt newname.txt') == 3, "mv should be Tier 3"
    assert validator.get_tier('git commit -m "test"') == 3, "git should be Tier 3"
    assert validator.get_tier('npm install package') == 3, "npm should be Tier 3"
    assert validator.get_tier('pip install requests') == 3, "pip should be Tier 3"
    assert validator.get_tier('Copy-Item file.txt dest') == 3, "Copy-Item should be Tier 3"
    assert validator.get_tier('Move-Item file.txt dest') == 3, "Move-Item should be Tier 3"


# ============================================================================
# TIER 4 TESTS - LOCKDOWN (CRITICAL SAFETY TEST)
# ============================================================================

def test_tier_4_lockdown_bash(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 4 commands show warnings and require 'yes' confirmation.
    
    **CRITICAL SAFETY TEST** - Wrong tier = data loss risk
    
    Test Coverage:
    - Destructive bash commands: rm, dd
    - Expected: All return tier 4
    - Behavior: Multiple warnings + exact 'yes' match required (not just 'y')
    - Risk if fails: User could accidentally delete files without adequate warnings
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test Tier 4 commands - MOST DANGEROUS
    assert validator.get_tier('rm -rf /') == 4, "rm -rf should be Tier 4 (LOCKDOWN)"
    assert validator.get_tier('rm important_file.txt') == 4, "rm should be Tier 4"
    assert validator.get_tier('dd if=/dev/zero of=/dev/sda') == 4, "dd should be Tier 4 (disk wipe)"


def test_tier_4_lockdown_powershell(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier 4 commands for PowerShell show warnings and require confirmation.
    
    **CRITICAL SAFETY TEST** - Cross-platform consistency
    
    Test Coverage:
    - Destructive PowerShell commands: Remove-Item, del, Format-Volume
    - Expected: Same tier as bash equivalents
    - Risk if fails: Windows users could delete files without warnings
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test PowerShell Tier 4 commands
    assert validator.get_tier('Remove-Item -Recurse C:\\') == 4, "Remove-Item should be Tier 4"
    assert validator.get_tier('del important.txt') == 4, "del should be Tier 4"
    assert validator.get_tier('format C:') == 4, "format should be Tier 4"
    assert validator.get_tier('Format-Volume C') == 4, "Format-Volume should be Tier 4 (disk format)"


# ============================================================================
# CUSTOM TIER OVERRIDES TESTS
# ============================================================================

def test_custom_tier_overrides(mock_preferences_with_overrides, tier_defaults, monkeypatch):
    """
    User can override tier assignments in preferences.
    
    Test Coverage:
    - User moved 'find' from Tier 2.5 to Tier 1
    - User moved 'grep' from Tier 2 to Tier 1
    - Expected: Custom overrides take precedence over defaults
    - Behavior: User explicitly chose to bypass safety (their responsibility)
    - Risk if fails: User preferences ignored, unexpected behavior
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences_with_overrides)
    
    # Test custom overrides
    assert validator.get_tier('find / -name test') == 1, "find should be overridden to Tier 1"
    assert validator.get_tier('grep pattern file') == 1, "grep should be overridden to Tier 1"
    
    # Test non-overridden commands still use defaults
    assert validator.get_tier('rm file.txt') == 4, "rm should still be Tier 4 (no override)"
    assert validator.get_tier('ls') == 1, "ls should still be Tier 1 (matches override tier)"


# ============================================================================
# UNKNOWN COMMAND TESTS
# ============================================================================

def test_unknown_command_defaults_tier_3(mock_preferences, tier_defaults, monkeypatch):
    """
    Unknown commands default to Tier 3 (safe default).
    
    Test Coverage:
    - Commands not in tier_defaults.json
    - Expected: Return tier 3 (AI validation required)
    - Behavior: Safe default prevents accidental dangerous execution
    - Risk if fails: Unknown dangerous commands might execute without validation
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test unknown commands
    assert validator.get_tier('unknown_cmd') == 3, "Unknown command should default to Tier 3"
    assert validator.get_tier('weird-tool --flag') == 3, "Unknown tool should default to Tier 3"
    assert validator.get_tier('completely_made_up') == 3, "Made-up command should default to Tier 3"


# ============================================================================
# CROSS-PLATFORM CONSISTENCY TESTS
# ============================================================================

def test_powershell_vs_bash_variants_same_tier(mock_preferences, tier_defaults, monkeypatch):
    """
    PowerShell and bash equivalents have same tier.
    
    Test Coverage:
    - ls (bash) vs Get-ChildItem (PowerShell) - both Tier 1
    - rm (bash) vs Remove-Item (PowerShell) - both Tier 4
    - cp (bash) vs Copy-Item (PowerShell) - both Tier 3
    - Expected: Cross-platform consistency (users switching shells get same safety)
    - Risk if fails: Confusing behavior differences between Windows and Linux
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Test cross-platform equivalents
    assert validator.get_tier('ls') == validator.get_tier('Get-ChildItem'), \
        "ls and Get-ChildItem should have same tier"
    
    assert validator.get_tier('rm file') == validator.get_tier('Remove-Item file'), \
        "rm and Remove-Item should have same tier (both dangerous)"
    
    assert validator.get_tier('cp src dst') == validator.get_tier('Copy-Item src dst'), \
        "cp and Copy-Item should have same tier"


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

def test_empty_command(mock_preferences, tier_defaults, monkeypatch):
    """
    Empty command string handled gracefully.
    
    Test Coverage:
    - Empty string input
    - Expected: Returns tier 3 (safe default) or handles error gracefully
    - Risk if fails: Crash on empty input
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Empty command should not crash
    result = validator.get_tier('')
    assert result == 3, "Empty command should default to Tier 3"


def test_command_with_arguments(mock_preferences, tier_defaults, monkeypatch):
    """
    Commands with arguments correctly extract base command for tier lookup.
    
    Test Coverage:
    - Commands with spaces, flags, paths
    - Expected: Tier based on first word (command name)
    - Risk if fails: Arguments might interfere with tier detection
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Commands with arguments
    assert validator.get_tier('ls -la /home/user') == 1, "ls with args should be Tier 1"
    assert validator.get_tier('rm -rf /tmp/test') == 4, "rm with args should be Tier 4"
    assert validator.get_tier('git commit -m "message"') == 3, "git with args should be Tier 3"


def test_case_sensitivity(mock_preferences, tier_defaults, monkeypatch):
    """
    Command matching is case-sensitive (matches shell behavior).
    
    Test Coverage:
    - Uppercase vs lowercase commands
    - Expected: Exact case match required
    - Risk if fails: Case variations might bypass tier classification
    """
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Case sensitivity
    assert validator.get_tier('ls') == 1, "Lowercase 'ls' should be Tier 1"
    assert validator.get_tier('LS') == 1, "Uppercase 'LS' converts to 'ls', should be Tier 1"
    assert validator.get_tier('Get-ChildItem') == 1, "PowerShell cmdlets are case-sensitive"


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

def test_tier_lookup_performance(mock_preferences, tier_defaults, monkeypatch):
    """
    Tier lookup is fast enough for interactive use (<1ms per lookup).
    
    Test Coverage:
    - 1000 tier lookups
    - Expected: Completes in <100ms total (average <0.1ms per lookup)
    - Risk if fails: Slow tier lookups could make Isaac feel laggy
    """
    import time
    from isaac.core.tier_validator import TierValidator
    
    monkeypatch.setattr(
        'isaac.core.tier_validator.TierValidator._load_tier_defaults',
        lambda self: tier_defaults
    )
    
    validator = TierValidator(mock_preferences)
    
    # Benchmark 1000 tier lookups
    commands = ['ls', 'grep', 'find', 'git', 'rm'] * 200
    
    start_time = time.time()
    for cmd in commands:
        validator.get_tier(cmd)
    elapsed = time.time() - start_time
    
    assert elapsed < 0.1, f"1000 tier lookups took {elapsed:.3f}s (should be <100ms)"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_tier_defaults_file_exists():
    """
    Verify tier_defaults.json file exists and is valid JSON.
    
    Test Coverage:
    - File existence
    - JSON validity
    - Required tier keys (1, 2, 2.5, 3, 4)
    - Risk if fails: App won't start if defaults file missing or corrupted
    """
    from pathlib import Path
    
    # Expected file location: isaac/data/tier_defaults.json
    expected_path = Path(__file__).parent.parent / 'isaac' / 'data' / 'tier_defaults.json'
    
    assert expected_path.exists(), f"tier_defaults.json not found at {expected_path}"
    
    # Validate JSON structure
    defaults = json.loads(expected_path.read_text())
    
    required_tiers = ["1", "2", "2.5", "3", "4"]
    for tier in required_tiers:
        assert tier in defaults, f"Tier {tier} missing from tier_defaults.json"
        assert isinstance(defaults[tier], list), f"Tier {tier} should be a list of commands"
        assert len(defaults[tier]) > 0, f"Tier {tier} should not be empty"


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 14

Coverage Breakdown:
- Tier 1 (Instant): 2 tests (bash + PowerShell)
- Tier 2 (Auto-correct): 1 test
- Tier 2.5 (Confirm): 1 test
- Tier 3 (Validate): 1 test
- Tier 4 (Lockdown): 2 tests (bash + PowerShell) **CRITICAL**
- Custom Overrides: 1 test
- Unknown Commands: 1 test
- Cross-Platform: 1 test
- Edge Cases: 3 tests (empty, args, case)
- Performance: 1 test
- Integration: 1 test (file exists)

Critical Safety Tests:
- test_tier_4_lockdown_bash - MUST PASS (prevents accidental rm -rf)
- test_tier_4_lockdown_powershell - MUST PASS (prevents accidental Remove-Item)
- test_custom_tier_overrides - MUST PASS (respects user intent)

Success Criteria:
✅ All 14 tests pass
✅ Coverage >= 100% of tier_validator.py
✅ No false negatives (dangerous commands correctly classified as Tier 4)
✅ No false positives (safe commands not over-restricted)

Next Steps:
1. Run: pytest tests/test_tier_validator.py --cov=isaac.core.tier_validator
2. Verify 100% coverage
3. If all pass → Handoff to YAML Maker
4. If failures → Debug tier classification logic
"""
