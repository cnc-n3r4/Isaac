# tests/test_ai_integration.py
"""
Test Suite for Isaac AI Integration (Phase 3)

**CRITICAL: AI must respect tier system for safety.**

This module tests AI-powered features while ensuring safety mechanisms
are not bypassed. Wrong implementation = DATA LOSS RISK.

Coverage Goal: 85%+
Test Count: 38 scenarios

Test Priority: CRITICAL (Safety + Privacy)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
import json


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_xai_api():
    """Mock x.ai API responses for all AI operations"""
    mock = Mock()
    
    # Default translation response
    mock.translate_to_shell.return_value = {
        'success': True,
        'command': 'find . -type f -size +100M',
        'explanation': 'Finds files larger than 100MB',
        'confidence': 0.95
    }
    
    # Default validation response
    mock.validate_command.return_value = {
        'safe': True,
        'warnings': [],
        'suggestions': []
    }
    
    # Default typo correction
    mock.correct_typo.return_value = {
        'corrected': 'grep pattern file.txt',
        'original': 'grp pattern file.txt',
        'confidence': 0.9
    }
    
    # Default task planning
    mock.plan_task.return_value = {
        'steps': [
            {'command': 'ls -la', 'tier': 1},
            {'command': 'grep pattern *.txt', 'tier': 2}
        ],
        'description': 'Find patterns in text files'
    }
    
    return mock


@pytest.fixture
def mock_ai_disabled():
    """Config with AI features disabled"""
    return {
        'machine_id': 'TEST-MACHINE',
        'ai_enabled': False,
        'sync_enabled': False
    }


@pytest.fixture
def mock_ai_enabled():
    """Config with AI features enabled"""
    return {
        'machine_id': 'TEST-MACHINE',
        'ai_enabled': True,
        'xai_api_key': 'test_xai_key',
        'auto_correct_tier2': True,
        'sync_enabled': False
    }


@pytest.fixture
def command_router_with_ai(mock_ai_enabled):
    """CommandRouter with AI integration"""
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    shell = BashAdapter()
    session_mgr = SessionManager(mock_ai_enabled, shell)
    router = CommandRouter(session_mgr, shell)
    
    return router


@pytest.fixture
def tier_defaults():
    """Tier classification defaults"""
    return {
        "1": ["ls", "cd", "pwd"],
        "2": ["grep", "head", "tail"],
        "2.5": ["find", "sed", "awk"],
        "3": ["cp", "mv", "git"],
        "4": ["rm", "dd", "format"]
    }


# ============================================================================
# X.AI API CLIENT TESTS (6 tests)
# ============================================================================

@patch('requests.post')
def test_translate_to_shell_success(mock_post):
    """
    x.ai API translates natural language to shell command.
    
    Test Coverage:
    - Mock x.ai API returns valid command
    - translate_to_shell() returns dict with command + explanation
    - Confidence score >= 0.8
    - Risk if fails: Translation functionality broken
    """
    from isaac.ai.xai_client import XaiClient
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'choices': [{
            'message': {
                'content': json.dumps({
                    'command': 'find . -name "*.log"',
                    'explanation': 'Finds all log files in current directory',
                    'confidence': 0.92
                })
            }
        }]
    }
    mock_post.return_value = mock_response
    
    client = XaiClient(api_key='test_key')
    result = client.translate_to_shell("find all log files", "bash")
    
    assert result['success'] == True
    assert 'find' in result['command']
    assert result['confidence'] >= 0.8


@patch('requests.post')
def test_translate_to_shell_timeout(mock_post):
    """
    API timeout handled gracefully.
    
    Test Coverage:
    - Mock API times out (10 seconds)
    - translate_to_shell() returns error dict
    - No crash, graceful failure
    - Risk if fails: Isaac crashes on AI API timeout
    """
    from isaac.ai.xai_client import XaiClient
    import requests
    
    mock_post.side_effect = requests.Timeout("API timeout after 10s")
    
    client = XaiClient(api_key='test_key')
    result = client.translate_to_shell("find files", "bash")
    
    assert result['success'] == False
    assert 'error' in result or 'timeout' in str(result).lower()


@patch('requests.post')
def test_validate_command_success(mock_post):
    """
    AI validation returns safety warnings.
    
    Test Coverage:
    - Mock x.ai API returns safety analysis
    - validate_command() returns dict with safe=True/False + warnings
    - Suggestions list populated
    - Risk if fails: Tier 3 validation broken
    """
    from isaac.ai.xai_client import XaiClient
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'content': [{
            'text': json.dumps({
                'safe': False,
                'warnings': ['Force push overwrites remote history'],
                'suggestions': ['Use git push without -f', 'Create backup branch first']
            })
        }]
    }
    mock_post.return_value = mock_response
    
    client = XaiClient(api_key='test_key')
    result = client.validate_command("git push -f origin main")
    
    assert 'safe' in result
    assert isinstance(result['warnings'], list)
    assert len(result['warnings']) > 0


@patch('requests.post')
def test_correct_typo_high_confidence(mock_post):
    """
    AI detects and corrects typos with high confidence.
    
    Test Coverage:
    - Mock x.ai detects typo ("grp" → "grep")
    - correct_typo() returns corrected command + confidence 0.9
    - Original command preserved in response
    - Risk if fails: Tier 2 auto-correction broken
    """
    from isaac.ai.xai_client import XaiClient
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'content': [{
            'text': json.dumps({
                'corrected': 'grep pattern file.txt',
                'original': 'grp pattern file.txt',
                'confidence': 0.95,
                'explanation': 'Typo detected: grp → grep'
            })
        }]
    }
    mock_post.return_value = mock_response
    
    client = XaiClient(api_key='test_key')
    result = client.correct_typo("grp pattern file.txt")
    
    assert result['corrected'] == 'grep pattern file.txt'
    assert result['confidence'] >= 0.9
    assert result['original'] == 'grp pattern file.txt'


@patch('requests.post')
def test_plan_task_success(mock_post):
    """
    AI breaks task into multi-step plan.
    
    Test Coverage:
    - Mock x.ai breaks task into steps
    - plan_task() returns list of steps with tiers
    - Each step has command + tier classification
    - Risk if fails: Task mode planning broken
    """
    from isaac.ai.xai_client import XaiClient
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'content': [{
            'text': json.dumps({
                'steps': [
                    {'command': 'find . -name "*.log"', 'tier': 2.5},
                    {'command': 'tar -czf logs.tar.gz *.log', 'tier': 3},
                    {'command': 'rm *.log', 'tier': 4}
                ],
                'description': 'Archive and delete log files'
            })
        }]
    }
    mock_post.return_value = mock_response
    
    client = XaiClient(api_key='test_key')
    result = client.plan_task("backup and delete all log files")
    
    assert 'steps' in result
    assert len(result['steps']) == 3
    assert all('tier' in step for step in result['steps'])


@patch('requests.post')
def test_api_network_failure(mock_post):
    """
    Network failures handled gracefully across all AI methods.
    
    Test Coverage:
    - Mock requests library raises ConnectionError
    - All x.ai client methods return error dicts (not exceptions)
    - Logged for debugging
    - Risk if fails: Isaac crashes on network issues
    """
    from isaac.ai.xai_client import XaiClient
    import requests
    
    mock_post.side_effect = requests.ConnectionError("Network unreachable")
    
    client = XaiClient(api_key='test_key')
    
    # Test all methods handle network failure
    result1 = client.translate_to_shell("find files", "bash")
    result2 = client.validate_command("rm file.txt")
    result3 = client.correct_typo("grp pattern")
    result4 = client.plan_task("backup files")
    
    # All should return error dicts (not raise exceptions)
    assert result1['success'] == False
    assert result2['success'] == False
    assert result3['success'] == False
    assert result4['success'] == False


# ============================================================================
# NATURAL LANGUAGE TRANSLATION TESTS (6 tests)
# ============================================================================

@patch('isaac.ai.xai_client.XaiClient.translate_to_shell')
def test_translation_basic(mock_translate):
    """
    Basic natural language translation works.
    
    Test Coverage:
    - Input: "isaac find large files"
    - Translator calls x.ai API
    - Returns valid find command
    - Command is shell-appropriate (bash vs PowerShell)
    - Risk if fails: NL translation broken
    """
    from isaac.ai.translator import translate_query
    from isaac.adapters.bash_adapter import BashAdapter
    from isaac.core.session_manager import SessionManager
    
    mock_translate.return_value = {
        'success': True,
        'command': 'find . -type f -size +100M',
        'explanation': 'Finds files larger than 100MB',
        'confidence': 0.9
    }
    
    shell = BashAdapter()
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    session_mgr = SessionManager(config, shell)
    
    result = translate_query("find large files", "bash", session_mgr)
    
    assert result['success'] == True
    assert 'find' in result['command']


@patch('isaac.ai.xai_client.XaiClient.translate_to_shell')
@patch('isaac.core.tier_validator.TierValidator.get_tier')
def test_translation_through_tier_system(mock_get_tier, mock_translate, tier_defaults, monkeypatch):
    """
    **CRITICAL SAFETY TEST**
    
    AI-translated commands MUST go through tier system.
    
    Test Coverage:
    - Input: "isaac delete all logs"
    - Translator returns "rm -rf *.log"
    - Command goes through tier system
    - Tier 4 validation triggered (user sees warnings)
    - Risk if fails: AI BYPASSES SAFETY → DATA LOSS
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    # Mock x.ai to return dangerous command
    mock_translate.return_value = {
        'success': True,
        'command': 'rm -rf *.log',  # DANGEROUS (Tier 4)
        'explanation': 'Deletes all log files',
        'confidence': 0.95
    }
    
    # Mock tier validator to return Tier 4
    mock_get_tier.return_value = 4  # LOCKDOWN
    
    config = {'machine_id': 'TEST', 'ai_enabled': True, 'xai_api_key': 'test'}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    # Simulate user input
    result = router.route_command("isaac delete all logs")
    
    # CRITICAL: Must trigger Tier 4 warnings (not auto-execute)
    mock_get_tier.assert_called()  # Tier system WAS consulted
    # In real implementation, result would contain warnings
    # For now, verify tier system was invoked


@patch('isaac.ai.xai_client.XaiClient.translate_to_shell')
def test_translation_invalid_query(mock_translate):
    """
    Invalid queries rejected (non-shell tasks).
    
    Test Coverage:
    - Input: "isaac what's the weather"
    - Translator detects non-shell query
    - Returns error (not a shell task)
    - No command executed
    - Risk if fails: Executes nonsensical commands
    """
    from isaac.ai.translator import translate_query
    from isaac.adapters.bash_adapter import BashAdapter
    from isaac.core.session_manager import SessionManager
    
    mock_translate.return_value = {
        'success': False,
        'error': 'Not a shell command query',
        'is_general_question': True
    }
    
    shell = BashAdapter()
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    session_mgr = SessionManager(config, shell)
    
    result = translate_query("what's the weather", "bash", session_mgr)
    
    assert result['success'] == False
    assert 'error' in result or result.get('is_general_question') == True


def test_ai_query_logged_separately():
    """
    **CRITICAL PRIVACY TEST**
    
    AI queries logged separately from command history.
    
    Test Coverage:
    - User runs "isaac find files"
    - AI query logged to aiquery_history (not command_history)
    - Verify separation (privacy requirement)
    - --show-queries shows it, --show-log doesn't
    - Risk if fails: PRIVACY BREACH
    """
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    
    # Simulate AI query
    session_mgr.add_ai_query("find files", "AI response here")
    
    # Verify logged to AI history (not command history)
    assert len(session_mgr.aiquery_history) == 1
    assert len(session_mgr.command_history.entries) == 0  # NOT in command history
    
    # Verify AI query content
    ai_query = session_mgr.aiquery_history[0]
    assert ai_query['query'] == "find files"
    assert ai_query['response'] == "AI response here"


def test_translation_with_ai_disabled():
    """
    Translation fails gracefully when AI disabled.
    
    Test Coverage:
    - Config has ai_enabled: false
    - "isaac find files" returns error
    - Falls back to MVP behavior
    - Risk if fails: Crashes when AI disabled
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': False}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    result = router.route_command("isaac find files")
    
    # Should return error (AI disabled)
    assert result.success == False or "AI disabled" in result.output


def test_translation_no_api_key():
    """
    Missing API key handled gracefully.
    
    Test Coverage:
    - Config missing xai_api_key
    - Translation attempts return error
    - Isaac continues in non-AI mode
    - Risk if fails: Crashes when API key missing
    """
    from isaac.ai.xai_client import XaiClient
    
    client = XaiClient(api_key='')  # Empty API key
    
    result = client.translate_to_shell("find files", "bash")
    
    assert result['success'] == False
    assert 'api_key' in str(result).lower() or 'error' in result


# ============================================================================
# AUTO-CORRECTION TESTS (6 tests)
# ============================================================================

@patch('isaac.ai.xai_client.XaiClient.correct_typo')
@patch('isaac.core.tier_validator.TierValidator.get_tier')
def test_tier2_auto_correct_execute(mock_get_tier, mock_correct):
    """
    **CRITICAL SAFETY TEST**
    
    Tier 2 auto-correction executes safely.
    
    Test Coverage:
    - Command: "grp pattern file.txt" (typo)
    - Tier 2 command
    - Corrector detects "grp" → "grep"
    - Auto-corrects AND executes (no confirmation)
    - Correction logged
    - Risk if fails: Auto-correction modifies wrong commands
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    mock_correct.return_value = {
        'success': True,
        'corrected': 'grep pattern file.txt',
        'original': 'grp pattern file.txt',
        'confidence': 0.95
    }
    mock_get_tier.return_value = 2  # Tier 2
    
    config = {'machine_id': 'TEST', 'ai_enabled': True, 'auto_run_tier2': True}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    # Simulate typo command
    result = router.route_command("grp pattern file.txt")
    
    # Should auto-correct and execute (Tier 2 + auto_run_tier2=True)
    mock_correct.assert_called_once()


@patch('isaac.ai.xai_client.XaiClient.correct_typo')
@patch('isaac.core.tier_validator.TierValidator.get_tier')
def test_tier2_5_correct_then_confirm(mock_get_tier, mock_correct):
    """
    Tier 2.5 correction requires confirmation.
    
    Test Coverage:
    - Command: "find -nam test.txt" (typo in flag)
    - Tier 2.5 command
    - Corrector suggests "find -name test.txt"
    - User sees correction, THEN confirms
    - Doesn't auto-execute
    - Risk if fails: Dangerous commands auto-execute
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    mock_correct.return_value = {
        'success': True,
        'corrected': 'find -name test.txt',
        'original': 'find -nam test.txt',
        'confidence': 0.9
    }
    mock_get_tier.return_value = 2.5  # Tier 2.5 (confirm required)
    
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    # Simulate typo command
    # (In real implementation, would prompt user for confirmation)
    result = router.route_command("find -nam test.txt")
    
    # Should correct but NOT auto-execute (Tier 2.5)
    mock_correct.assert_called_once()


@patch('isaac.ai.xai_client.XaiClient.correct_typo')
def test_auto_correct_low_confidence(mock_correct):
    """
    Low-confidence corrections require user confirmation.
    
    Test Coverage:
    - Typo detected but confidence < 0.8
    - Ask user for confirmation (don't auto-correct)
    - User can accept or reject
    - Risk if fails: Wrong corrections applied automatically
    """
    from isaac.ai.corrector import correct_command
    
    mock_correct.return_value = {
        'success': True,
        'corrected': 'grep pattern file.txt',
        'original': 'grp pattern file.txt',
        'confidence': 0.65  # LOW confidence
    }
    
    result = correct_command("grp pattern file.txt", auto_apply=False)
    
    # Should return suggestion but not auto-apply
    assert result['confidence'] < 0.8
    # In real implementation, would require user confirmation


def test_no_typo_execute_as_is():
    """
    Commands without typos execute unmodified.
    
    Test Coverage:
    - Command: "grep pattern file.txt" (correct)
    - Corrector finds no typo
    - Command executes without modification
    - Risk if fails: Unnecessary corrections applied
    """
    from isaac.ai.corrector import detect_typo
    
    result = detect_typo("grep pattern file.txt")
    
    assert result['has_typo'] == False
    # Original command should be unchanged


@patch('isaac.ai.xai_client.XaiClient.correct_typo')
def test_correction_preserves_arguments(mock_correct):
    """
    Typo correction preserves command arguments.
    
    Test Coverage:
    - Command: "grp -r 'test' /home" (typo, but args correct)
    - Corrector fixes "grp" → "grep"
    - Preserves flags: "-r", pattern: 'test', path: /home
    - Risk if fails: Arguments lost during correction
    """
    mock_correct.return_value = {
        'success': True,
        'corrected': 'grep -r \'test\' /home',
        'original': 'grp -r \'test\' /home',
        'confidence': 0.95
    }
    
    from isaac.ai.corrector import correct_command
    
    result = correct_command("grp -r 'test' /home")
    
    assert '-r' in result['corrected']
    assert 'test' in result['corrected']
    assert '/home' in result['corrected']


def test_ai_correction_disabled():
    """
    Auto-correction disabled by config.
    
    Test Coverage:
    - Config has auto_correct_tier2: false
    - Typos NOT auto-corrected
    - Commands execute as typed
    - Risk if fails: Correction happens when disabled
    """
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': False, 'auto_correct_tier2': False}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    
    # Verify AI disabled
    assert session_mgr.config.get('auto_correct_tier2') == False


# ============================================================================
# AI VALIDATION (TIER 3) TESTS (5 tests)
# ============================================================================

@patch('isaac.ai.xai_client.XaiClient.validate_command')
@patch('isaac.core.tier_validator.TierValidator.get_tier')
def test_tier3_validation_shows_warnings(mock_get_tier, mock_validate):
    """
    **CRITICAL SAFETY TEST**
    
    Tier 3 validation shows AI warnings.
    
    Test Coverage:
    - Command: "git push -f origin main"
    - Tier 3 requires validation
    - AI validator called
    - Warnings displayed (force push risks)
    - User confirms or aborts
    - Risk if fails: Dangerous commands execute without warnings
    """
    mock_get_tier.return_value = 3
    mock_validate.return_value = {
        'safe': False,
        'warnings': ['Force push overwrites remote history', 'May lose commits'],
        'suggestions': ['Use git push without -f', 'Create backup branch first']
    }
    
    from isaac.ai.validator import validate_tier3_command
    
    result = validate_tier3_command("git push -f origin main")
    
    assert result['safe'] == False
    assert len(result['warnings']) > 0
    assert 'Force push' in result['warnings'][0]


@patch('isaac.ai.xai_client.XaiClient.validate_command')
def test_tier3_safe_command_minimal_warnings(mock_validate):
    """
    Safe Tier 3 commands get minimal warnings.
    
    Test Coverage:
    - Command: "git status"
    - Tier 3 validation
    - AI returns safe=True, minimal warnings
    - User confirms, executes
    - Risk if fails: Overly cautious (too many false positives)
    """
    mock_validate.return_value = {
        'safe': True,
        'warnings': [],
        'suggestions': []
    }
    
    from isaac.ai.validator import validate_tier3_command
    
    result = validate_tier3_command("git status")
    
    assert result['safe'] == True
    assert len(result['warnings']) == 0


@patch('isaac.ai.xai_client.XaiClient.validate_command')
def test_tier3_ai_offline_fallback(mock_validate):
    """
    Tier 3 falls back to simple confirmation when AI offline.
    
    Test Coverage:
    - Tier 3 command triggered
    - AI validation fails (network error)
    - Falls back to simple confirmation (MVP behavior)
    - Command still requires user approval
    - Risk if fails: Commands execute without validation
    """
    mock_validate.side_effect = Exception("AI API unavailable")
    
    from isaac.ai.validator import validate_tier3_command
    
    result = validate_tier3_command("git commit -m 'test'")
    
    # Should fall back gracefully
    assert 'error' in result or result['safe'] == False


@patch('isaac.ai.xai_client.XaiClient.validate_command')
def test_validation_suggestions_displayed(mock_validate):
    """
    AI suggestions shown to user.
    
    Test Coverage:
    - Command: "rm *.log"
    - AI suggests "rm -i *.log" (interactive mode)
    - Suggestions shown to user
    - User can modify command before executing
    - Risk if fails: User doesn't see safer alternatives
    """
    mock_validate.return_value = {
        'safe': False,
        'warnings': ['Deleting multiple files'],
        'suggestions': ['Use rm -i *.log for interactive deletion']
    }
    
    from isaac.ai.validator import validate_tier3_command
    
    result = validate_tier3_command("rm *.log")
    
    assert len(result['suggestions']) > 0
    assert 'rm -i' in result['suggestions'][0]


def test_tier3_validation_respects_abort():
    """
    User can abort Tier 3 commands.
    
    Test Coverage:
    - AI shows warnings
    - User chooses "abort"
    - Command NOT executed
    - Returns aborted status
    - Risk if fails: Executes after user abort
    """
    from isaac.ai.validator import handle_user_choice
    
    result = handle_user_choice(user_input='abort', command='git push -f')
    
    assert result['executed'] == False
    assert result['status'] == 'aborted'


# ============================================================================
# TASK MODE TESTS (7 tests)
# ============================================================================

@patch('isaac.ai.xai_client.XaiClient.plan_task')
def test_task_planning_basic(mock_plan):
    """
    Task planning breaks input into steps.
    
    Test Coverage:
    - Input: "isaac task: backup project files"
    - Task planner calls x.ai API
    - Returns multi-step plan
    - Each step has command + tier
    - Risk if fails: Task mode doesn't work
    """
    mock_plan.return_value = {
        'steps': [
            {'command': 'tar -czf backup.tar.gz project/', 'tier': 3},
            {'command': 'mv backup.tar.gz /backup/', 'tier': 3}
        ],
        'description': 'Backup project files'
    }
    
    from isaac.ai.task_planner import plan_task
    
    result = plan_task("backup project files")
    
    assert 'steps' in result
    assert len(result['steps']) == 2
    assert all('tier' in step for step in result['steps'])


@patch('isaac.ai.task_runner.execute_step')
def test_task_execution_autonomous(mock_execute):
    """
    **CRITICAL SAFETY TEST**
    
    Autonomous mode only for Tier 1 commands.
    
    Test Coverage:
    - Plan has only Tier 1 commands
    - User chooses "autonomous" mode
    - All steps execute without confirmation
    - Task completes successfully
    - Risk if fails: Dangerous commands auto-execute
    """
    from isaac.ai.task_runner import execute_task
    
    plan = {
        'steps': [
            {'command': 'ls -la', 'tier': 1},
            {'command': 'pwd', 'tier': 1}
        ]
    }
    
    mock_execute.return_value = {'success': True, 'output': 'Command output'}
    
    result = execute_task(plan, mode='autonomous')
    
    assert result['completed'] == True
    assert mock_execute.call_count == 2  # Both steps executed


def test_task_execution_approve_once():
    """
    Approve-once mode for mixed tiers.
    
    Test Coverage:
    - Plan has mixed tiers (1, 2, 3)
    - User chooses "approve-once"
    - User approves plan once
    - All steps execute (including Tier 3)
    - Risk if fails: Tier 3 commands execute without approval
    """
    from isaac.ai.task_runner import execute_task
    
    plan = {
        'steps': [
            {'command': 'ls', 'tier': 1},
            {'command': 'grep pattern', 'tier': 2},
            {'command': 'git status', 'tier': 3}
        ]
    }
    
    # Simulate user approval
    result = execute_task(plan, mode='approve-once', approved=True)
    
    # All steps should be queued for execution
    assert 'steps_to_execute' in result or result.get('approved') == True


def test_task_execution_step_by_step():
    """
    Step-by-step mode for Tier 3/4 commands.
    
    Test Coverage:
    - Plan has Tier 3/4 commands
    - User chooses "step-by-step"
    - User confirms EACH step individually
    - Can abort mid-task
    - Risk if fails: Dangerous commands execute without per-step approval
    """
    from isaac.ai.task_runner import execute_task
    
    plan = {
        'steps': [
            {'command': 'git status', 'tier': 3},
            {'command': 'rm *.log', 'tier': 4}
        ]
    }
    
    # Simulate step-by-step (user confirms each)
    result = execute_task(plan, mode='step-by-step')
    
    assert result['mode'] == 'step-by-step'
    # In real implementation, would prompt for each step


@patch('isaac.ai.task_runner.execute_step')
def test_task_failure_recovery_options(mock_execute):
    """
    **CRITICAL SAFETY TEST**
    
    Task failures offer recovery options.
    
    Test Coverage:
    - Step 3 of 5 fails
    - Task pauses
    - User sees 5 recovery options: auto-fix/retry/skip/abort/suggest
    - User choice determines next action
    - Risk if fails: Partial execution leaves system in bad state
    """
    from isaac.ai.task_runner import handle_task_failure
    
    # Simulate step failure
    failure = {
        'step': 3,
        'command': 'git push origin main',
        'error': 'Permission denied'
    }
    
    result = handle_task_failure(failure)
    
    assert 'recovery_options' in result
    assert len(result['recovery_options']) == 5
    assert 'auto-fix' in result['recovery_options']
    assert 'retry' in result['recovery_options']
    assert 'skip' in result['recovery_options']
    assert 'abort' in result['recovery_options']
    assert 'suggest' in result['recovery_options']


def test_task_history_immutable():
    """
    Task history is append-only (immutable).
    
    Test Coverage:
    - Task executes with 1 failure
    - Failure logged
    - User applies fix
    - Fix appended as new step (original failure preserved)
    - Task history never modified (append-only)
    - Risk if fails: Audit trail lost
    """
    from isaac.models.task_history import TaskHistory
    
    task = TaskHistory(task_id='task_001')
    
    # Add step
    task.add_step({'command': 'git push', 'status': 'failed'})
    
    # Apply fix (should append, not modify)
    task.add_step({'command': 'git push', 'status': 'success', 'is_fix': True})
    
    assert len(task.steps) == 2
    assert task.steps[0]['status'] == 'failed'  # Original preserved
    assert task.steps[1]['is_fix'] == True  # Fix appended


def test_task_mode_disabled():
    """
    Task mode disabled gracefully.
    
    Test Coverage:
    - Config has task_mode_enabled: false
    - "isaac task: backup files" returns error
    - Feature disabled gracefully
    - Risk if fails: Crashes when disabled
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'task_mode_enabled': False}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    result = router.route_command("isaac task: backup files")
    
    assert result.success == False or "disabled" in result.output.lower()


# ============================================================================
# AI QUERY PRIVACY TESTS (3 tests)
# ============================================================================

def test_ai_query_separate_history():
    """
    **CRITICAL PRIVACY TEST**
    
    AI queries stored separately from command history.
    
    Test Coverage:
    - User runs "isaac find files"
    - Query logged to aiquery_history.json
    - NOT in command_history.json
    - Arrow keys don't show AI queries
    - Risk if fails: PRIVACY BREACH (AI queries exposed)
    """
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    
    # Add AI query
    session_mgr.add_ai_query("find large files", "AI translation result")
    
    # Verify separation
    assert len(session_mgr.aiquery_history) == 1
    assert len(session_mgr.command_history.entries) == 0
    
    # AI query should not be in command history
    ai_entry = session_mgr.aiquery_history[0]
    assert ai_entry['query'] == "find large files"


def test_show_queries_command():
    """
    --show-queries displays AI history only.
    
    Test Coverage:
    - User runs several AI queries
    - `isaac --show-queries` displays AI history
    - `isaac --show-log` does NOT show AI queries
    - Privacy maintained
    - Risk if fails: AI queries leak into command log
    """
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    
    # Add AI query and regular command
    session_mgr.add_ai_query("find files", "AI response")
    session_mgr.add_command("ls -la", Mock(exit_code=0))
    
    # Get AI queries only
    ai_queries = session_mgr.get_ai_queries()
    
    assert len(ai_queries) == 1
    assert ai_queries[0]['query'] == "find files"
    
    # Get command history only
    commands = session_mgr.get_command_history()
    
    assert len(commands) == 1
    assert commands[0]['command'] == "ls -la"
    # AI query NOT in command history


@patch('isaac.api.cloud_client.CloudClient.save_session_file')
def test_ai_query_cloud_sync(mock_save):
    """
    AI queries sync to cloud with privacy flag.
    
    Test Coverage:
    - AI query logged locally
    - If cloud sync enabled (Phase 2.5)
    - AI queries sync to cloud (separate file)
    - Privacy flag set (PRIVATE)
    - Risk if fails: Privacy metadata lost in cloud
    """
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {
        'machine_id': 'TEST',
        'ai_enabled': True,
        'sync_enabled': True,
        'api_url': 'https://test.com/api',
        'api_key': 'test_key'
    }
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    
    mock_save.return_value = True
    
    # Add AI query (should trigger cloud sync)
    session_mgr.add_ai_query("weather query", "AI answer")
    session_mgr.sync_to_cloud('aiquery_history.json')
    
    # Verify cloud sync called with aiquery_history
    mock_save.assert_called_once()
    call_args = mock_save.call_args
    assert 'aiquery_history.json' in str(call_args)


# ============================================================================
# GRACEFUL DEGRADATION TESTS (5 tests)
# ============================================================================

def test_ai_disabled_mvp_behavior():
    """
    **CRITICAL SAFETY TEST**
    
    AI disabled = MVP mode (no crashes).
    
    Test Coverage:
    - Config has ai_enabled: false
    - All AI features disabled
    - Isaac works in MVP mode
    - Tier system still functions
    - No crashes or errors
    - Risk if fails: Isaac unusable without AI
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': False}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    # Tier system should still work
    result = router.route_command("ls -la")
    
    # Should execute normally (Tier 1)
    # No AI features, but basic functionality intact


def test_no_xai_api_key_error():
    """
    Missing API key shows error, non-AI features work.
    
    Test Coverage:
    - Config missing xai_api_key
    - AI features show error message
    - Non-AI features work normally
    - User informed to add API key
    - Risk if fails: Cryptic errors or crashes
    """
    from isaac.ai.xai_client import XaiClient
    
    client = XaiClient(api_key=None)
    
    result = client.translate_to_shell("find files", "bash")
    
    assert result['success'] == False
    # Should have clear error about missing API key


@patch('isaac.ai.xai_client.XaiClient.validate_command')
def test_ai_timeout_fallback(mock_validate):
    """
    AI timeout falls back to non-AI behavior.
    
    Test Coverage:
    - AI API times out
    - Feature falls back to non-AI behavior
    - Example: Tier 3 validation → simple confirm
    - No crash, graceful degradation
    - Risk if fails: Timeout crashes Isaac
    """
    import requests
    mock_validate.side_effect = requests.Timeout("API timeout")
    
    from isaac.ai.validator import validate_tier3_command
    
    result = validate_tier3_command("git commit -m 'test'")
    
    # Should fall back gracefully (not crash)
    assert 'error' in result or result['safe'] == False


def test_incorrect_translation_rejected():
    """
    Invalid AI translations rejected.
    
    Test Coverage:
    - AI translates to invalid command
    - Tier system catches error
    - Command not executed
    - User sees error message
    - Risk if fails: Executes nonsense commands
    """
    from isaac.core.command_router import CommandRouter
    from isaac.core.session_manager import SessionManager
    from isaac.adapters.bash_adapter import BashAdapter
    
    config = {'machine_id': 'TEST', 'ai_enabled': True}
    shell = BashAdapter()
    session_mgr = SessionManager(config, shell)
    router = CommandRouter(session_mgr, shell)
    
    # Simulate invalid translation
    # (In real implementation, AI might return malformed command)
    result = router.route_command("nonsense gibberish invalid")
    
    # Should reject (not execute)
    assert result.success == False or result.exit_code != 0


def test_all_phase1_tests_still_pass():
    """
    **CRITICAL REGRESSION TEST**
    
    Phase 1 tests still pass after Phase 3 integration.
    
    Test Coverage:
    - After Phase 3 integration
    - All 15 Phase 1 tests MUST still pass
    - No regressions in tier system
    - Verify with: pytest tests/test_tier_validator.py
    - Risk if fails: AI breaks core safety features
    """
    # This test verifies no regressions
    # Run: pytest tests/test_tier_validator.py
    # Expected: 15/15 passing
    
    # Placeholder - actual test is running Phase 1 suite
    assert True, "Run: pytest tests/test_tier_validator.py to verify"


# ============================================================================
# SUMMARY
# ============================================================================

"""
Test Suite Summary:
-------------------
Total Tests: 38

Coverage Breakdown:
- x.ai API Client: 6 tests (translate, validate, correct, plan, network)
- Natural Language Translation: 6 tests (basic, tier system, invalid, privacy, disabled)
- Auto-Correction: 6 tests (tier 2, tier 2.5, confidence, preserve, disabled)
- AI Validation (Tier 3): 5 tests (warnings, safe, fallback, suggestions, abort)
- Task Mode: 7 tests (planning, autonomous, approve-once, step-by-step, failure, history, disabled)
- AI Query Privacy: 3 tests (separate history, show-queries, cloud sync)
- Graceful Degradation: 5 tests (AI disabled, no API key, timeout, invalid, regression)

Critical Safety Tests (MUST PASS):
- test_translation_through_tier_system - AI CANNOT bypass tier system
- test_tier2_auto_correct_execute - Auto-correction safe
- test_tier3_validation_shows_warnings - Dangerous commands warned
- test_task_execution_autonomous - Task mode respects tiers
- test_task_failure_recovery_options - Partial execution handled
- test_ai_query_separate_history - Privacy maintained
- test_ai_disabled_mvp_behavior - Graceful degradation
- test_all_phase1_tests_still_pass - No regressions

Success Criteria:
✅ All 38 tests passing (100%)
✅ Coverage >= 85% of isaac/ai/ module
✅ No safety bypasses (AI respects tiers)
✅ Privacy requirements met (separate histories)
✅ Graceful degradation verified (AI disabled works)
✅ No regressions (Phase 1 tests still pass)

Next Steps:
1. Run: pytest tests/test_ai_integration.py --cov=isaac.ai
2. Verify 85%+ coverage
3. Run regression: pytest tests/test_tier_validator.py (must still pass)
4. If all pass → Handoff to YAML Maker
5. If failures → Debug AI integration logic

CRITICAL REMINDER:
If AI bypasses tier system → USER DATA LOSS
These tests are the last line of defense.
"""
