#!/usr/bin/env python3
"""
Test script for Command Consolidation features
"""

import tempfile
from pathlib import Path
from isaac.commands.help_unified.run import UnifiedHelpCommand
from isaac.core.flag_parser import FlagParser, parse_flags
from isaac.core.aliases import AliasManager, add_alias, resolve_alias
from isaac.core.command_history import CommandHistory, add_command_to_history, get_recent_history


def test_unified_help():
    """Test unified help system"""
    print("Testing Unified Help System...")

    help_cmd = UnifiedHelpCommand()

    # Test basic help listing
    result = help_cmd.run([])
    assert "ISAAC Commands Reference" in result
    print("✅ Basic help listing works")

    # Test search functionality
    result = help_cmd.run(["--search", "file"])
    assert "Commands matching 'file'" in result
    print("✅ Search functionality works")

    # Test whatis functionality
    result = help_cmd.run(["--whatis", "/help"])
    assert "/help:" in result
    print("✅ Whatis functionality works")

    # Test man functionality
    result = help_cmd.run(["--man", "isaac"])
    assert "ISAAC - AI-Enhanced" in result
    print("✅ Manual page functionality works")

    print("🎉 Unified Help System tests completed!")


def test_flag_parser():
    """Test flag parser utility"""
    print("\nTesting Flag Parser...")

    parser = FlagParser()

    # Test basic flag parsing
    result = parser.parse(["--verbose", "--output", "file.txt", "input.txt"])
    assert result.get_flag("verbose") == True
    assert result.get_flag("output") == "file.txt"
    assert result.positional_args == ["input.txt"]
    print("✅ Basic flag parsing works")

    # Test short flags
    result = parser.parse(["-v", "-f", "value"])
    print(f"Debug: flags = {result.flags}")
    assert result.get_flag("verbose") == True
    assert result.get_flag("force") == "value"  # 'f' gets resolved to 'force'
    print("✅ Short flag parsing works")

    # Test flag aliases
    result = parser.parse(["-h", "-s", "query"])
    assert result.get_flag("help") == True
    assert result.get_flag("search") == "query"
    print("✅ Flag aliases work")

    print("🎉 Flag Parser tests completed!")


def test_aliases():
    """Test command aliases system"""
    print("\nTesting Command Aliases...")

    with tempfile.TemporaryDirectory() as temp_dir:
        aliases_file = Path(temp_dir) / 'test_aliases.json'
        manager = AliasManager(aliases_file)

        # Test adding aliases
        success = manager.add_alias("ll", "ls -la", "Long listing")
        assert success == True
        print("✅ Adding aliases works")

        # Test resolving aliases
        command = manager.resolve_alias("ll")
        assert command == "ls -la"
        print("✅ Resolving aliases works")

        # Test listing aliases
        aliases = manager.list_aliases()
        assert len(aliases) == 1
        assert aliases[0].name == "ll"
        print("✅ Listing aliases works")

        # Test search
        results = manager.search_aliases("list")
        assert len(results) == 1
        print("✅ Searching aliases works")

        # Test export/import
        exported = manager.export_aliases()
        assert len(exported) == 1

        new_manager = AliasManager(Path(temp_dir) / 'imported_aliases.json')
        imported = new_manager.import_aliases(exported)
        assert imported == 1
        print("✅ Export/import works")

    print("🎉 Command Aliases tests completed!")


def test_command_history():
    """Test command history system"""
    print("\nTesting Command History...")

    with tempfile.TemporaryDirectory() as temp_dir:
        history_file = Path(temp_dir) / 'test_history.json'
        history = CommandHistory(history_file, max_entries=100)

        # Test adding entries
        history.add_entry("ls -la", success=True, execution_time=0.5)
        history.add_entry("git status", success=True, execution_time=0.2)
        history.add_entry("invalid_command", success=False, execution_time=0.1)
        print("✅ Adding history entries works")

        # Test getting recent history
        recent = history.get_recent(5)
        assert len(recent) == 3
        assert recent[0].command == "invalid_command"  # Most recent first
        print("✅ Getting recent history works")

        # Test search
        results = history.search_history("git")
        assert len(results) == 1
        assert "git status" in results[0].command
        print("✅ History search works")

        # Test frequency analysis
        frequent = history.get_commands_by_frequency(2)
        assert len(frequent) == 2
        print("✅ Frequency analysis works")

        # Test failed commands
        failed = history.get_failed_commands(5)
        assert len(failed) == 1
        assert failed[0].command == "invalid_command"
        print("✅ Failed commands retrieval works")

        # Test export/import
        export_file = Path(temp_dir) / 'exported_history.json'
        success = history.export_history(export_file)
        assert success == True

        new_history = CommandHistory(Path(temp_dir) / 'imported_history.json')
        imported = new_history.import_history(export_file)
        assert imported == 3
        print("✅ History export/import works")

        # Test statistics
        stats = history.get_stats()
        assert stats['total_commands'] == 3
        assert stats['successful_commands'] == 2
        assert stats['failed_commands'] == 1
        print("✅ History statistics work")

    print("🎉 Command History tests completed!")


def main():
    """Run all tests"""
    print("🧪 Testing Command Consolidation Features")
    print("=" * 50)

    try:
        test_unified_help()
        test_flag_parser()
        test_aliases()
        test_command_history()

        print("\n🎉 All Command Consolidation tests passed!")
        print("Phase 1 Command Consolidation is complete! ✅")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()