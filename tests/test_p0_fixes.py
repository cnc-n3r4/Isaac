"""
Test suite for P0 critical fixes
Tests prefix enforcement, strip logic, and casual pattern recognition
"""
import pytest
from isaac.core.cli_command_router import CommandRouter, CommandResult
from isaac.core.session_manager import SessionManager
from isaac.core.ai_translator import AITranslator


@pytest.fixture
def session():
    """Create test session"""
    return SessionManager()


@pytest.fixture
def router(session):
    """Create router with test session"""
    return CommandRouter(session)


@pytest.fixture
def translator():
    """Create AI translator for testing"""
    return AITranslator()


# ============================================================================
# P0-1: PREFIX ENFORCEMENT TESTS
# ============================================================================

def test_bare_natural_language_rejected(router):
    """
    Test that bare natural language (no 'isaac' prefix) is rejected.

    User types: "hello"
    Expected: Error with helpful message
    """
    result = router.execute("hello")

    assert not result.success, "Bare command should fail"
    assert result.status_symbol == '⊘', "Should use error symbol"
    assert "I have a name" in result.message, "Should have helpful error message"
    assert result.suggestion and "isaac" in result.suggestion, "Should suggest prefix"
    assert result.metadata and result.metadata.get("error_type") == "missing_prefix"


def test_bare_question_rejected(router):
    """
    Test that bare questions are also rejected.

    User types: "what time is it"
    Expected: Error requiring prefix
    """
    result = router.execute("what time is it")

    assert not result.success
    assert "I have a name" in result.message
    assert "isaac what time is it" in result.suggestion
    assert result.metadata and result.metadata.get("error_type") == "missing_prefix"


def test_prefixed_natural_language_accepted(router):
    """
    Test that prefixed commands are NOT rejected (may fail later, but not at prefix check).

    User types: "isaac hello"
    Expected: Passes prefix check (gets to translator)
    """
    result = router.execute("isaac hello")

    # Should NOT be rejected with prefix error
    assert "I have a name" not in result.message, "Should not reject prefixed command"
    # May fail at translation stage, but not at prefix enforcement


def test_shell_commands_bypass_prefix_check(router):
    """
    Test that shell/internal commands don't require prefix.

    User types: "ls" or "help"
    Expected: Should work without prefix
    """
    # Internal commands should work
    result_help = router.execute("help")
    assert "I have a name" not in result_help.message

    # Shell commands should be passed through
    result_ls = router.execute("ls")
    assert "I have a name" not in result_ls.message


def test_case_insensitive_prefix_check(router):
    """
    Test that prefix check is case-insensitive.

    User types: "ISAAC hello" or "Isaac hello"
    Expected: Should pass prefix check
    """
    result_upper = router.execute("ISAAC hello")
    assert "I have a name" not in result_upper.message

    result_mixed = router.execute("Isaac hello")
    assert "I have a name" not in result_mixed.message


# ============================================================================
# P0-2: STRIP PREFIX TESTS
# ============================================================================

def test_isaac_prefix_stripped_before_translation(translator):
    """
    Test that translator receives input WITHOUT 'isaac' prefix.

    This simulates what the router should do:
    1. User types: "isaac hello"
    2. Router strips to: "hello"
    3. Translator receives: "hello"
    4. Translator finds casual pattern
    """
    # Simulate the router's strip logic
    original = "isaac hello"
    stripped = original[6:].strip() if original.lower().startswith("isaac ") else original

    # Now translator should match casual pattern
    result = translator.translate(stripped)

    assert result is not None, "Should find pattern after stripping"
    assert result.confidence > 0.0, "Should have confidence in match"
    # After P0-3 implementation, this will match casual patterns
    # For now, just verify it's not None


def test_strip_preserves_case_of_query(translator):
    """
    Test that stripping only removes prefix, preserves query case.

    User types: "isaac What Time Is It"
    Stripped: "What Time Is It"
    Pattern matching should still work (case-insensitive)
    """
    original = "isaac What Time Is It"
    stripped = original[6:].strip() if original.lower().startswith("isaac ") else original

    assert stripped == "What Time Is It", "Should preserve query case"

    result = translator.translate(stripped)
    # Should still match patterns (translator does case-insensitive matching)
    assert result is not None


def test_strip_handles_multiple_spaces(translator):
    """
    Test handling of extra spaces after prefix.

    User types: "isaac    hello" (extra spaces)
    Stripped: "hello" (spaces trimmed)
    """
    original = "isaac    hello"
    stripped = original[6:].strip() if original.lower().startswith("isaac ") else original

    assert stripped == "hello", "Should trim extra spaces"

    result = translator.translate(stripped)
    assert result is not None


def test_no_strip_if_no_prefix(translator):
    """
    Test that input without prefix is left unchanged.

    This shouldn't happen in normal flow (prefix check would reject it),
    but defensive programming requires handling it.
    """
    original = "hello"
    stripped = original[6:].strip() if original.lower().startswith("isaac ") else original

    assert stripped == "hello", "Should not modify if no prefix"


def test_strip_case_insensitive(translator):
    """
    Test that stripping works with different case variations.

    "ISAAC hello" -> "hello"
    "Isaac hello" -> "hello"
    "iSaAc hello" -> "hello"
    """
    test_cases = [
        ("ISAAC hello", "hello"),
        ("Isaac hello", "hello"),
        ("iSaAc hello", "hello"),
        ("isaac HELLO", "HELLO"),  # Preserves query case
    ]

    for original, expected in test_cases:
        stripped = original[6:].strip() if original.lower().startswith("isaac ") else original
        assert stripped == expected, f"Failed for input: {original}"


# ============================================================================
# P0-3: CASUAL PATTERN TESTS
# ============================================================================

def test_greeting_hello(translator):
    """Test basic 'hello' greeting"""
    result = translator.translate("hello")

    assert result is not None, "Should match casual pattern"
    assert result.confidence > 0.8, "Should have high confidence"
    assert result.metadata["operation"] == "chat"
    assert result.metadata["type"] == "greeting"
    assert result.translated == "chat"


def test_greeting_hi(translator):
    """Test 'hi' greeting"""
    result = translator.translate("hi")

    assert result is not None
    assert result.confidence >= 0.9
    assert result.metadata["type"] == "greeting"


def test_greeting_hey_there(translator):
    """Test 'hey there' greeting with optional word"""
    result = translator.translate("hey there")

    assert result is not None
    assert result.metadata["type"] == "greeting"


def test_greeting_good_morning(translator):
    """Test time-based greeting"""
    result = translator.translate("good morning")

    assert result is not None
    assert result.confidence >= 0.9
    assert result.metadata["type"] == "greeting"


def test_greeting_how_are_you(translator):
    """Test conversational greeting"""
    result = translator.translate("how are you")

    assert result is not None
    assert result.metadata["type"] == "greeting"


def test_greeting_whats_up(translator):
    """Test casual greeting"""
    result = translator.translate("what's up")

    assert result is not None
    assert result.metadata["type"] == "greeting"


def test_question_what_is(translator):
    """Test 'what is' question pattern"""
    result = translator.translate("what is Python")

    assert result is not None
    assert result.confidence >= 0.7
    assert result.metadata["operation"] == "query"
    assert result.metadata["type"] == "question"
    assert "python" in result.metadata["subject"].lower()


def test_question_when_is(translator):
    """Test 'when is' question pattern"""
    result = translator.translate("when is the meeting")

    assert result is not None
    assert result.metadata["type"] == "question"
    assert "meeting" in result.metadata["subject"]


def test_question_where_is(translator):
    """Test 'where is' question pattern"""
    result = translator.translate("where is the file")

    assert result is not None
    assert result.metadata["type"] == "question"
    assert "file" in result.metadata["subject"]


def test_question_why_do(translator):
    """Test 'why' question pattern"""
    result = translator.translate("why do we use backups")

    assert result is not None
    assert result.metadata["type"] == "question"
    assert "backups" in result.metadata["subject"]


def test_question_how_can(translator):
    """Test 'how can' question pattern"""
    result = translator.translate("how can I restore")

    assert result is not None
    assert result.metadata["type"] == "question"


def test_question_can_you(translator):
    """Test 'can you' question pattern"""
    result = translator.translate("can you help me")

    assert result is not None
    assert result.metadata["type"] == "question"
    assert "help me" in result.metadata["subject"]


def test_time_query(translator):
    """Test 'what time is it' query"""
    result = translator.translate("what time is it")

    assert result is not None
    assert result.confidence >= 0.8
    assert result.metadata["operation"] == "info"
    assert result.metadata["info_type"] == "time"
    assert result.translated == "info"


def test_date_query(translator):
    """Test date query"""
    result = translator.translate("what's the date")

    assert result is not None
    assert result.metadata["operation"] == "info"
    assert result.metadata["info_type"] == "time"


def test_weather_query(translator):
    """Test weather query"""
    result = translator.translate("what's the weather")

    assert result is not None
    assert result.confidence >= 0.8
    assert result.metadata["operation"] == "info"
    assert result.metadata["info_type"] == "weather"


def test_weather_condition_query(translator):
    """Test specific weather condition"""
    result = translator.translate("is it raining")

    assert result is not None
    assert result.metadata["info_type"] == "weather"


def test_case_insensitive_patterns(translator):
    """Test that patterns work regardless of case"""
    test_cases = [
        "HELLO",
        "Hello",
        "HeLLo",
        "WHAT TIME IS IT",
        "What's The Weather",
    ]

    for query in test_cases:
        result = translator.translate(query)
        assert result is not None, f"Failed for: {query}"
        assert result.confidence > 0.7, f"Low confidence for: {query}"


def test_pattern_priority_order(translator):
    """Test that existing patterns (backup/restore) still take priority"""
    # These should still match existing command patterns, not casual
    result_backup = translator.translate("backup everything")
    assert "backup" in result_backup.translated.lower()

    result_restore = translator.translate("restore my files")
    assert "restore" in result_restore.translated.lower()

    result_list = translator.translate("list backups")
    assert "list" in result_list.translated.lower()


def test_no_false_positives(translator):
    """Test that random strings don't match casual patterns"""
    # These should NOT match casual patterns
    random_strings = [
        "xyzabc123",
        "   ",
        "...",
    ]

    for query in random_strings:
        result = translator.translate(query)
        # Should either return None or very low confidence
        if result:
            assert result.confidence < 0.5, f"False positive for: {query}"