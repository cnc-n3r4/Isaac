"""
Test Generation - Create tests for reproducing and preventing bugs
Isaac's intelligent test generation system for comprehensive bug prevention
"""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class TestCase:
    """Represents a generated test case."""

    test_id: str
    title: str
    description: str
    test_type: str  # 'unit', 'integration', 'regression', 'performance'
    code: str
    setup_code: str
    assertions: List[str]
    expected_behavior: str
    prerequisites: List[str]
    tags: List[str]


@dataclass
class TestSuite:
    """Collection of related test cases."""

    suite_name: str
    description: str
    test_cases: List[TestCase]
    setup_code: str
    teardown_code: str
    dependencies: List[str]


@dataclass
class BugReproductionTest:
    """Test specifically designed to reproduce a bug."""

    bug_id: str
    error_message: str
    reproduction_steps: List[str]
    test_code: str
    expected_failure: str
    success_criteria: str


class TestGenerator:
    """Generates comprehensive tests for bug reproduction and prevention."""

    def __init__(self):
        """Initialize the test generator."""
        self.test_templates = self._load_test_templates()
        self.language_patterns = self._load_language_patterns()

    def _load_test_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load test templates for different scenarios."""
        return {
            "command_failure": {
                "template": '''
def test_{command_name}_failure_{error_type}(self):
    """Test that {command_name} fails appropriately with {error_type}."""
    # Setup
    {setup_code}

    # Execute command that should fail
    with self.assertRaises({exception_type}):
        result = run_command("{command}")

    # Verify error message
    self.assertIn("{error_message}", str(result.exception))
''',
                "imports": ["unittest", "subprocess"],
                "setup": "def run_command(cmd): return subprocess.run(cmd, shell=True, capture_output=True, text=True)",
            },
            "permission_denied": {
                "template": '''
def test_{resource}_permission_denied(self):
    """Test permission denied scenario for {resource}."""
    # Setup: Create file/directory with restricted permissions
    {setup_code}

    # Attempt access without permissions
    with self.assertRaises(PermissionError):
        {access_code}

    # Cleanup
    {cleanup_code}
''',
                "imports": ["unittest", "os", "stat"],
                "setup": "import tempfile; import shutil",
            },
            "resource_exhaustion": {
                "template": '''
def test_{resource}_exhaustion_handling(self):
    """Test handling of {resource} exhaustion."""
    # Setup: Simulate resource exhaustion
    {setup_code}

    # Execute operation that exhausts resources
    with self.assertRaises({exception_type}):
        {exhaustion_code}

    # Verify graceful degradation
    self.assertTrue(system_has_recovered())
''',
                "imports": ["unittest", "psutil", "resource"],
                "setup": "import psutil; import resource",
            },
            "network_failure": {
                "template": '''
def test_network_{operation}_failure(self):
    """Test {operation} failure with network issues."""
    # Setup: Simulate network failure
    {setup_code}

    # Attempt network operation
    with self.assertRaises({exception_type}):
        {network_code}

    # Verify timeout and error handling
    self.assertLess(operation_duration(), {timeout} * 2)
''',
                "imports": ["unittest", "socket", "time"],
                "setup": "import socket; import time",
            },
            "file_operation": {
                "template": '''
def test_file_{operation}_robustness(self):
    """Test file {operation} with various edge cases."""
    test_cases = [
        ("normal_file", "normal content"),
        ("empty_file", ""),
        ("large_file", "x" * 1000000),
        ("special_chars_file", "special: !@#$%^&*()"),
        ("unicode_file", "unicode: ñáéíóú 🚀"),
    ]

    for filename, content in test_cases:
        with self.subTest(filename=filename):
            # Setup
            {setup_code}

            # Execute file operation
            result = {operation_code}

            # Verify result
            {assertion_code}

            # Cleanup
            {cleanup_code}
''',
                "imports": ["unittest", "tempfile", "os"],
                "setup": "import tempfile; import os",
            },
        }

    def _load_language_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load language-specific test patterns."""
        return {
            "python": {
                "test_frameworks": ["unittest", "pytest"],
                "assertion_patterns": {
                    "equality": "self.assertEqual({actual}, {expected})",
                    "exception": "with self.assertRaises({exception}): {code}",
                    "truth": "self.assertTrue({condition})",
                    "false": "self.assertFalse({condition})",
                },
                "test_file_pattern": "test_*.py",
                "test_class_pattern": "Test*",
            },
            "javascript": {
                "test_frameworks": ["jest", "mocha"],
                "assertion_patterns": {
                    "equality": "expect({actual}).toBe({expected})",
                    "exception": "expect(() => { {code} }).toThrow({exception})",
                    "truth": "expect({condition}).toBeTruthy()",
                    "false": "expect({condition}).toBeFalsy()",
                },
                "test_file_pattern": "*.test.js",
                "test_class_pattern": "describe",
            },
        }

    def generate_bug_reproduction_test(
        self, error_message: str, diagnostic_data: Dict[str, Any], root_cause: str = None
    ) -> BugReproductionTest:
        """Generate a test that reproduces a specific bug.

        Args:
            error_message: The original error message
            diagnostic_data: Diagnostic information
            root_cause: Identified root cause

        Returns:
            Test designed to reproduce the bug
        """
        bug_id = f"bug_{int(time.time())}"
        error_type = self._categorize_error(error_message)

        # Generate reproduction steps
        reproduction_steps = self._generate_reproduction_steps(error_type, diagnostic_data)

        # Generate test code
        test_code = self._generate_reproduction_test_code(error_type, diagnostic_data)

        # Determine expected failure
        expected_failure = self._determine_expected_failure(error_type, error_message)

        # Define success criteria
        success_criteria = (
            "Test should fail with the exact error message when bug conditions are met"
        )

        return BugReproductionTest(
            bug_id=bug_id,
            error_message=error_message,
            reproduction_steps=reproduction_steps,
            test_code=test_code,
            expected_failure=expected_failure,
            success_criteria=success_criteria,
        )

    def generate_regression_test_suite(self, error_history: List[Dict[str, Any]]) -> TestSuite:
        """Generate a test suite to prevent regression of past errors.

        Args:
            error_history: List of past errors and their fixes

        Returns:
            Comprehensive test suite
        """
        suite_name = "regression_test_suite"
        description = "Test suite to prevent regression of previously fixed bugs"

        test_cases = []

        for error_data in error_history:
            test_case = self._generate_regression_test(error_data)
            if test_case:
                test_cases.append(test_case)

        setup_code = """
import unittest
import subprocess
import tempfile
import os
import sys
"""

        teardown_code = """
# Cleanup temporary files and resources
"""

        dependencies = ["unittest", "subprocess", "tempfile"]

        return TestSuite(
            suite_name=suite_name,
            description=description,
            test_cases=test_cases,
            setup_code=setup_code,
            teardown_code=teardown_code,
            dependencies=dependencies,
        )

    def generate_edge_case_tests(self, command: str, context: Dict[str, Any]) -> List[TestCase]:
        """Generate tests for edge cases of a command.

        Args:
            command: The command to test
            context: Command context and usage patterns

        Returns:
            List of edge case test cases
        """
        test_cases = []

        # Common edge cases
        edge_cases = [
            {
                "name": "empty_input",
                "description": "Test behavior with empty input",
                "input": "",
                "expected": "graceful_handling",
            },
            {
                "name": "large_input",
                "description": "Test behavior with very large input",
                "input": "x" * 1000000,
                "expected": "no_crash",
            },
            {
                "name": "special_characters",
                "description": "Test behavior with special characters",
                "input": "!@#$%^&*()[]{}|;:,.<>?",
                "expected": "proper_escaping",
            },
            {
                "name": "unicode_input",
                "description": "Test behavior with unicode characters",
                "input": "ñáéíóú 🚀 🌟",
                "expected": "unicode_support",
            },
            {
                "name": "concurrent_execution",
                "description": "Test behavior when run concurrently",
                "input": "normal_input",
                "expected": "no_race_conditions",
            },
        ]

        for edge_case in edge_cases:
            test_case = self._generate_edge_case_test(command, edge_case)
            test_cases.append(test_case)

        return test_cases

    def generate_performance_tests(
        self, command: str, performance_profile: Dict[str, Any]
    ) -> List[TestCase]:
        """Generate performance regression tests.

        Args:
            command: The command to test
            performance_profile: Performance baseline data

        Returns:
            Performance test cases
        """
        test_cases = []

        # Performance baseline test
        baseline_test = TestCase(
            test_id=f"perf_baseline_{int(time.time())}",
            title=f"Performance baseline for {command}",
            description="Ensure command performance doesn't regress below baseline",
            test_type="performance",
            code=f"""
def test_{command.replace(' ', '_')}_performance_baseline(self):
    \"\"\"Test that {command} meets performance baseline.\"\"\"
    import time
    start_time = time.time()

    # Execute command
    result = subprocess.run({repr(command)}, shell=True, capture_output=True)

    end_time = time.time()
    duration = end_time - start_time

    # Assert performance meets baseline
    baseline_duration = {performance_profile.get('duration', 1.0)}
    self.assertLess(duration, baseline_duration * 1.5)  # Allow 50% degradation
    self.assertEqual(result.returncode, 0)
""",
            setup_code="import subprocess; import time",
            assertions=[f"duration < {performance_profile.get('duration', 1.0) * 1.5}"],
            expected_behavior="Command completes within performance baseline",
            prerequisites=["Performance baseline established"],
            tags=["performance", "regression"],
        )

        test_cases.append(baseline_test)

        # Resource usage test
        resource_test = TestCase(
            test_id=f"perf_resource_{int(time.time())}",
            title=f"Resource usage test for {command}",
            description="Ensure command doesn't exceed resource limits",
            test_type="performance",
            code=f"""
def test_{command.replace(' ', '_')}_resource_usage(self):
    \"\"\"Test that {command} stays within resource limits.\"\"\"
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_percent()

    # Execute command
    result = subprocess.run({repr(command)}, shell=True, capture_output=True)

    final_memory = process.memory_percent()
    memory_increase = final_memory - initial_memory

    # Assert memory usage is reasonable
    self.assertLess(memory_increase, 50.0)  # Less than 50% memory increase
    self.assertEqual(result.returncode, 0)
""",
            setup_code="import subprocess; import psutil; import os",
            assertions=["memory_increase < 50.0"],
            expected_behavior="Command uses reasonable system resources",
            prerequisites=["psutil available"],
            tags=["performance", "resource"],
        )

        test_cases.append(resource_test)

        return test_cases

    def _categorize_error(self, error_message: str) -> str:
        """Categorize error for test generation."""
        error_lower = error_message.lower()

        if re.search(r"command not found|is not recognized", error_lower):
            return "command_not_found"
        elif re.search(r"permission denied|access is denied", error_lower):
            return "permission_denied"
        elif re.search(r"out of memory|cannot allocate memory", error_lower):
            return "out_of_memory"
        elif re.search(r"no space left|disk full", error_lower):
            return "disk_full"
        elif re.search(r"connection refused|connection timed out", error_lower):
            return "connection_refused"
        else:
            return "unknown_error"

    def _generate_reproduction_steps(
        self, error_type: str, diagnostic_data: Dict[str, Any]
    ) -> List[str]:
        """Generate steps to reproduce an error."""
        steps = []

        if error_type == "command_not_found":
            steps = [
                "Ensure the command is not installed",
                "Attempt to execute the command",
                "Verify the error message appears",
            ]
        elif error_type == "permission_denied":
            steps = [
                "Create a file or directory",
                "Remove read/write/execute permissions",
                "Attempt to access the resource",
                "Verify permission denied error",
            ]
        elif error_type == "out_of_memory":
            steps = [
                "Consume most available memory",
                "Execute memory-intensive operation",
                "Verify out of memory error occurs",
            ]
        elif error_type == "disk_full":
            steps = ["Fill up disk space", "Attempt to write to disk", "Verify disk full error"]
        elif error_type == "connection_refused":
            steps = [
                "Stop the target service",
                "Attempt to connect to the service",
                "Verify connection refused error",
            ]

        return steps

    def _generate_reproduction_test_code(
        self, error_type: str, diagnostic_data: Dict[str, Any]
    ) -> str:
        """Generate test code to reproduce an error."""
        template = self.test_templates.get(error_type, self.test_templates["command_failure"])

        # Fill in template variables
        variables = {
            "command_name": diagnostic_data.get("command", "").split()[0] or "unknown_command",
            "error_type": error_type,
            "setup_code": self._generate_setup_code(error_type, diagnostic_data),
            "exception_type": self._map_error_to_exception(error_type),
            "error_message": diagnostic_data.get("error_message", ""),
            "command": diagnostic_data.get("command", ""),
            "resource": diagnostic_data.get("resource", "resource"),
            "access_code": self._generate_access_code(error_type, diagnostic_data),
            "cleanup_code": self._generate_cleanup_code(error_type),
            "operation": diagnostic_data.get("operation", "operation"),
            "network_code": self._generate_network_code(error_type, diagnostic_data),
            "timeout": diagnostic_data.get("timeout", 30),
            "operation_code": self._generate_operation_code(error_type),
            "assertion_code": self._generate_assertion_code(error_type),
        }

        try:
            test_code = template["template"].format(**variables)
            return test_code.strip()
        except KeyError as e:
            return f"# Error generating test code: missing variable {e}"

    def _generate_setup_code(self, error_type: str, diagnostic_data: Dict[str, Any]) -> str:
        """Generate setup code for test."""
        if error_type == "permission_denied":
            return """
import tempfile
import os
import stat

# Create temporary file with restricted permissions
temp_file = tempfile.NamedTemporaryFile(delete=False)
temp_file.close()
os.chmod(temp_file.name, stat.S_IRUSR)  # Read-only for owner
test_file = temp_file.name
"""
        elif error_type == "out_of_memory":
            return """
import resource
import sys

# Set memory limit
resource.setrlimit(resource.RLIMIT_AS, (100 * 1024 * 1024, 200 * 1024 * 1024))  # 100MB limit
"""
        elif error_type == "disk_full":
            return """
import tempfile
import os

# Create temporary directory
temp_dir = tempfile.mkdtemp()
# Fill disk space (simplified)
"""
        else:
            return "# Setup code for test"

    def _map_error_to_exception(self, error_type: str) -> str:
        """Map error type to Python exception."""
        mapping = {
            "command_not_found": "FileNotFoundError",
            "permission_denied": "PermissionError",
            "out_of_memory": "MemoryError",
            "disk_full": "OSError",
            "connection_refused": "ConnectionError",
        }
        return mapping.get(error_type, "Exception")

    def _generate_access_code(self, error_type: str, diagnostic_data: Dict[str, Any]) -> str:
        """Generate code that attempts to access a resource."""
        if error_type == "permission_denied":
            return "with open(test_file, 'w') as f: f.write('test')"
        else:
            return "pass  # Access code"

    def _generate_cleanup_code(self, error_type: str) -> str:
        """Generate cleanup code for test."""
        if error_type == "permission_denied":
            return "os.unlink(test_file)"
        else:
            return "pass  # Cleanup code"

    def _generate_network_code(self, error_type: str, diagnostic_data: Dict[str, Any]) -> str:
        """Generate network operation code."""
        return """
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('localhost', 12345))  # Non-existent service
"""

    def _generate_operation_code(self, error_type: str) -> str:
        """Generate operation code for file tests."""
        return "perform_file_operation(filename, content)"

    def _generate_assertion_code(self, error_type: str) -> str:
        """Generate assertion code."""
        return "self.assertIsNotNone(result)"

    def _determine_expected_failure(self, error_type: str, error_message: str) -> str:
        """Determine the expected failure behavior."""
        return f"Should raise {self._map_error_to_exception(error_type)} with message containing error details"

    def _generate_regression_test(self, error_data: Dict[str, Any]) -> Optional[TestCase]:
        """Generate a regression test for a past error."""
        error_message = error_data.get("error_message", "")
        if not error_message:
            return None

        error_type = self._categorize_error(error_message)

        test_code = self._generate_reproduction_test_code(error_type, error_data)

        return TestCase(
            test_id=f"regression_{int(time.time())}",
            title=f"Regression test for: {error_message[:50]}...",
            description="Ensure this previously fixed bug doesn't reoccur",
            test_type="regression",
            code=test_code,
            setup_code="import unittest",
            assertions=["self.assertTrue(True)  # Bug should not occur"],
            expected_behavior="Command executes without the previous error",
            prerequisites=["Bug has been fixed"],
            tags=["regression", error_type],
        )

    def _generate_edge_case_test(self, command: str, edge_case: Dict[str, Any]) -> TestCase:
        """Generate a test for a specific edge case."""
        return TestCase(
            test_id=f"edge_{edge_case['name']}_{int(time.time())}",
            title=f"Edge case: {edge_case['name']} for {command}",
            description=edge_case["description"],
            test_type="unit",
            code=f"""
def test_{command.replace(' ', '_')}_{edge_case['name']}(self):
    \"\"\"{edge_case['description']}\"\"\"
    # Setup
    input_data = {repr(edge_case['input'])}

    # Execute command
    result = subprocess.run({repr(command)}, input=input_data,
                          shell=True, capture_output=True, text=True)

    # Verify expected behavior: {edge_case['expected']}
    self.assertEqual(result.returncode, 0)
""",
            setup_code="import subprocess",
            assertions=["result.returncode == 0"],
            expected_behavior=edge_case["expected"],
            prerequisites=["Command available"],
            tags=["edge_case", edge_case["name"]],
        )

    def write_test_file(self, test_suite: TestSuite, output_path: Path) -> bool:
        """Write a test suite to a file.

        Args:
            test_suite: The test suite to write
            output_path: Path to write the test file

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, "w") as f:
                # Write imports
                f.write("import unittest\n")
                for dep in test_suite.dependencies:
                    f.write(f"import {dep}\n")
                f.write("\n")

                # Write setup code
                if test_suite.setup_code.strip():
                    f.write(test_suite.setup_code)
                    f.write("\n\n")

                # Write test class
                f.write(f"class {test_suite.suite_name}(unittest.TestCase):\n")
                f.write(f'    """{test_suite.description}"""\n\n')

                # Write test methods
                for test_case in test_suite.test_cases:
                    f.write(f"    def {test_case.test_id}(self):\n")
                    f.write(f'        """{test_case.title}"""\n')

                    # Write setup code
                    if test_case.setup_code:
                        for line in test_case.setup_code.split("\n"):
                            if line.strip():
                                f.write(f"        {line}\n")

                    # Write test code
                    for line in test_case.code.split("\n"):
                        if line.strip():
                            f.write(f"        {line}\n")

                    f.write("\n")

                # Write teardown code
                if test_suite.teardown_code.strip():
                    f.write("    def tearDown(self):\n")
                    for line in test_suite.teardown_code.split("\n"):
                        if line.strip():
                            f.write(f"        {line}\n")
                    f.write("\n")

                # Write main block
                f.write("if __name__ == '__main__':\n")
                f.write("    unittest.main()\n")

            return True

        except Exception as e:
            print(f"Error writing test file: {e}")
            return False

    def run_generated_test(self, test_file: Path) -> Dict[str, Any]:
        """Run a generated test file and return results.

        Args:
            test_file: Path to the test file

        Returns:
            Test execution results
        """
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_file), "-v"],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": getattr(result, "duration", None),
            }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Test execution timed out", "return_code": -1}
        except Exception as e:
            return {"success": False, "error": str(e), "return_code": -1}
