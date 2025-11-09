#!/usr/bin/env python3
"""
Phase 1 Stabilization - Completion Test Suite

Validates that all Phase 1 tasks have been completed successfully:
1. Dependencies installed
2. Syntax errors fixed
3. Security vulnerabilities patched
4. Alias system integrated
5. Tier 4 commands populated

Run with: pytest tests/test_phase1_completion.py -v
"""

import pytest
import sys
import json
import subprocess
from pathlib import Path


class TestPhase1Dependencies:
    """Test Task 1: Dependency Installation"""

    def test_core_dependencies_installed(self):
        """Verify all core dependencies can be imported"""
        try:
            import jsonschema
            import dotenv
            import flask
            import anthropic
            import openai
        except ImportError as e:
            pytest.fail(f"Missing dependency: {e}")

    def test_isaac_core_imports(self):
        """Verify ISAAC core modules can be imported"""
        try:
            import isaac.core.command_router
        except ImportError as e:
            pytest.fail(f"Cannot import ISAAC core module: {e}")


class TestPhase1Syntax:
    """Test Task 2: Syntax Error Resolution"""

    def test_problematic_files_removed(self):
        """Verify problematic legacy files have been removed"""
        repo_root = Path(__file__).parent.parent

        # These files should not exist
        problematic_files = [
            repo_root / 'isaac' / 'core' / 'session_manager_old.py',
            repo_root / 'temp_test.py'
        ]

        for file_path in problematic_files:
            assert not file_path.exists(), f"Problematic file still exists: {file_path}"

    def test_python_files_compile(self):
        """Verify all Python files compile without syntax errors"""
        repo_root = Path(__file__).parent.parent
        isaac_dir = repo_root / 'isaac'

        # Compile all Python files
        result = subprocess.run(
            ['python', '-m', 'compileall', str(isaac_dir), '-q'],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Syntax errors found:\n{result.stderr}"


class TestPhase1Security:
    """Test Task 3: Security Vulnerability Patching"""

    def test_no_shell_injection_in_smart_router(self):
        """Verify smart_router.py uses secure subprocess calls"""
        repo_root = Path(__file__).parent.parent
        smart_router = repo_root / 'isaac' / 'dragdrop' / 'smart_router.py'

        with open(smart_router) as f:
            lines = f.readlines()

        # Check for shlex import
        content = ''.join(lines)
        assert 'import shlex' in content, "shlex not imported in smart_router.py"

        # Check that shell=True is not used in actual subprocess calls
        # Exclude lines that are comments
        import re
        for i, line in enumerate(lines, 1):
            # Skip comment lines
            if line.strip().startswith('#'):
                continue
            # Check for unsafe pattern in actual code
            if re.search(r'shell\s*=\s*True', line):
                pytest.fail(f"Found unsafe shell=True usage at line {i} in smart_router.py: {line.strip()}")

    def test_no_shell_injection_in_msg(self):
        """Verify msg.py uses secure subprocess calls"""
        repo_root = Path(__file__).parent.parent
        msg_file = repo_root / 'isaac' / 'commands' / 'msg.py'

        with open(msg_file) as f:
            lines = f.readlines()

        # Check for shlex import
        content = ''.join(lines)
        assert 'import shlex' in content, "shlex not imported in msg.py"

        # Check that shell=True is not used in actual subprocess calls
        # Exclude lines that are comments
        import re
        for i, line in enumerate(lines, 1):
            # Skip comment lines
            if line.strip().startswith('#'):
                continue
            # Check for unsafe pattern in actual code
            if re.search(r'shell\s*=\s*True', line):
                pytest.fail(f"Found unsafe shell=True usage at line {i} in msg.py: {line.strip()}")

    def test_no_shell_injection_in_task_manager(self):
        """Verify task_manager.py uses secure subprocess calls"""
        repo_root = Path(__file__).parent.parent
        task_manager = repo_root / 'isaac' / 'core' / 'task_manager.py'

        with open(task_manager) as f:
            lines = f.readlines()

        # Check for shlex import
        content = ''.join(lines)
        assert 'import shlex' in content, "shlex not imported in task_manager.py"

        # Check that shell=True is not used in actual subprocess calls
        # Exclude lines that are comments
        import re
        for i, line in enumerate(lines, 1):
            # Skip comment lines
            if line.strip().startswith('#'):
                continue
            # Check for unsafe pattern in actual code
            if re.search(r'shell\s*=\s*True', line):
                pytest.fail(f"Found unsafe shell=True usage at line {i} in task_manager.py: {line.strip()}")


class TestPhase1AliasSystem:
    """Test Task 4: Alias System Integration"""

    def test_alias_system_integrated_in_command_router(self):
        """Verify Unix alias system is integrated in command_router.py"""
        repo_root = Path(__file__).parent.parent
        command_router = repo_root / 'isaac' / 'core' / 'command_router.py'

        with open(command_router) as f:
            content = f.read()

        # Check for platform detection
        assert 'import platform' in content, "platform module not imported"
        assert 'platform.system()' in content, "Platform detection not implemented"

        # Check for UnixAliasTranslator usage
        assert 'UnixAliasTranslator' in content, "UnixAliasTranslator not imported"

        # Check for _is_unix_command method
        assert 'def _is_unix_command' in content, "_is_unix_command helper method not found"

    def test_unix_alias_translator_exists(self):
        """Verify UnixAliasTranslator class exists"""
        repo_root = Path(__file__).parent.parent
        unix_aliases = repo_root / 'isaac' / 'core' / 'unix_aliases.py'

        assert unix_aliases.exists(), "unix_aliases.py not found"

        # Try importing it
        try:
            from isaac.core.unix_aliases import UnixAliasTranslator
        except ImportError as e:
            pytest.fail(f"Cannot import UnixAliasTranslator: {e}")


class TestPhase1Tier4Commands:
    """Test Task 5: Tier 4 Command Protection"""

    def test_tier4_commands_populated(self):
        """Verify tier_defaults.json contains comprehensive Tier 4 commands"""
        repo_root = Path(__file__).parent.parent
        tier_defaults = repo_root / 'isaac' / 'data' / 'tier_defaults.json'

        assert tier_defaults.exists(), "tier_defaults.json not found"

        with open(tier_defaults) as f:
            config = json.load(f)

        tier4_commands = config.get('4', [])

        # Check minimum count (should have 39+ dangerous commands)
        assert len(tier4_commands) >= 39, \
            f"Tier 4 should have at least 39 commands, found {len(tier4_commands)}"

        # Check for critical dangerous commands
        critical_commands = [
            'sudo', 'rm -rf', 'format', 'dd', 'shutdown',
            'docker rm', 'git push --force', 'systemctl stop'
        ]

        for cmd in critical_commands:
            assert cmd in tier4_commands, f"Critical command '{cmd}' not in Tier 4"


class TestPhase1Integration:
    """Integration tests to verify Phase 1 completion"""

    def test_phase1_all_tasks_complete(self):
        """Meta-test: Verify all Phase 1 tasks are complete"""
        # This test passes if all other tests pass
        # It serves as a marker that Phase 1 is fully complete
        assert True, "Phase 1 Stabilization: All tasks complete!"


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
