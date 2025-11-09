"""Plugin Development Kit - Tools for developing Isaac plugins."""

import json
from pathlib import Path
from typing import Optional, Dict, Any, List


PLUGIN_TEMPLATE = '''"""{{name}} - {{description}}

Author: {{author}}
Version: {{version}}
"""

from isaac.plugins.plugin_api import Plugin, PluginMetadata, PluginContext, PluginHook


class {{class_name}}(Plugin):
    """{{description}}"""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="{{name}}",
            version="{{version}}",
            author="{{author}}",
            description="{{description}}",
            license="{{license}}",
            tags={{tags}},
            hooks=[{{hooks}}],
            commands={{commands}},
            permissions={{permissions}},
        )

    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin.

        Args:
            context: Plugin context
        """
        self._context = context

        # Register hooks
        {{hook_registrations}}

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        pass

    # Hook handlers
    {{hook_handlers}}
'''

HOOK_HANDLER_TEMPLATE = '''
    def on_{{hook_name}}(self) -> None:
        """Handle {{hook_name}} hook."""
        # TODO: Implement handler
        pass
'''

README_TEMPLATE = '''# {{name}}

{{description}}

## Installation

```bash
isaac plugin install {{name}}
```

## Usage

{{usage}}

## Configuration

{{configuration}}

## Hooks

This plugin registers the following hooks:
{{hook_list}}

## Permissions

This plugin requires the following permissions:
{{permission_list}}

## License

{{license}}

## Author

{{author}}
'''

MANIFEST_TEMPLATE = '''{
    "name": "{{name}}",
    "version": "{{version}}",
    "author": "{{author}}",
    "description": "{{description}}",
    "homepage": "{{homepage}}",
    "repository": "{{repository}}",
    "license": "{{license}}",
    "tags": {{tags}},
    "requires_isaac_version": ">=3.0.0",
    "dependencies": [],
    "hooks": {{hooks}},
    "commands": {{commands}},
    "permissions": {{permissions}}
}
'''

TEST_TEMPLATE = '''"""Tests for {{name}} plugin."""

import unittest
from isaac.plugins.plugin_api import PluginContext
from plugin import {{class_name}}


class Test{{class_name}}(unittest.TestCase):
    """Test suite for {{class_name}}."""

    def setUp(self):
        """Set up test fixtures."""
        self.plugin = {{class_name}}()
        self.context = PluginContext(
            session_id="test",
            workspace_path="/tmp",
            config={},
        )

    def test_metadata(self):
        """Test plugin metadata."""
        metadata = self.plugin.metadata
        self.assertEqual(metadata.name, "{{name}}")
        self.assertEqual(metadata.version, "{{version}}")

    def test_initialize(self):
        """Test plugin initialization."""
        self.plugin.initialize(self.context)
        # Add initialization tests

    def test_shutdown(self):
        """Test plugin shutdown."""
        self.plugin.initialize(self.context)
        self.plugin.shutdown()
        # Add shutdown tests


if __name__ == "__main__":
    unittest.main()
'''


class PluginDevKit:
    """Development kit for creating plugins."""

    def __init__(self, workspace_dir: Optional[Path] = None):
        """Initialize the development kit.

        Args:
            workspace_dir: Directory for plugin development
        """
        self.workspace_dir = workspace_dir or Path.cwd()

    def create_plugin(
        self,
        name: str,
        author: str,
        description: str,
        version: str = "0.1.0",
        license: str = "MIT",
        tags: Optional[List[str]] = None,
        hooks: Optional[List[str]] = None,
        commands: Optional[List[str]] = None,
        permissions: Optional[List[str]] = None,
        output_dir: Optional[Path] = None,
    ) -> Path:
        """Create a new plugin from template.

        Args:
            name: Plugin name
            author: Author name
            description: Plugin description
            version: Plugin version
            license: Plugin license
            tags: Plugin tags
            hooks: Hook names to register
            commands: Command names to register
            permissions: Required permissions
            output_dir: Output directory (defaults to workspace_dir/name)

        Returns:
            Path to created plugin directory
        """
        tags = tags or []
        hooks = hooks or []
        commands = commands or []
        permissions = permissions or []

        # Create output directory
        output_dir = output_dir or self.workspace_dir / name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate class name
        class_name = "".join(word.capitalize() for word in name.split("-"))
        if not class_name.endswith("Plugin"):
            class_name += "Plugin"

        # Generate hook registrations
        hook_registrations = []
        for hook in hooks:
            handler_name = f"on_{hook.lower()}"
            hook_registrations.append(
                f'        self.register_hook(PluginHook.{hook.upper()}, self.{handler_name})'
            )
        hook_registrations_str = "\n".join(hook_registrations) if hook_registrations else "        pass"

        # Generate hook handlers
        hook_handlers = []
        for hook in hooks:
            handler = HOOK_HANDLER_TEMPLATE.replace("{{hook_name}}", hook.lower())
            hook_handlers.append(handler)
        hook_handlers_str = "\n".join(hook_handlers) if hook_handlers else ""

        # Format hooks for metadata
        hooks_str = ", ".join([f"PluginHook.{hook.upper()}" for hook in hooks])

        # Generate plugin.py
        plugin_code = PLUGIN_TEMPLATE
        plugin_code = plugin_code.replace("{{name}}", name)
        plugin_code = plugin_code.replace("{{class_name}}", class_name)
        plugin_code = plugin_code.replace("{{author}}", author)
        plugin_code = plugin_code.replace("{{description}}", description)
        plugin_code = plugin_code.replace("{{version}}", version)
        plugin_code = plugin_code.replace("{{license}}", license)
        plugin_code = plugin_code.replace("{{tags}}", json.dumps(tags))
        plugin_code = plugin_code.replace("{{hooks}}", hooks_str)
        plugin_code = plugin_code.replace("{{commands}}", json.dumps(commands))
        plugin_code = plugin_code.replace("{{permissions}}", json.dumps(permissions))
        plugin_code = plugin_code.replace("{{hook_registrations}}", hook_registrations_str)
        plugin_code = plugin_code.replace("{{hook_handlers}}", hook_handlers_str)

        # Write plugin.py
        (output_dir / "plugin.py").write_text(plugin_code)

        # Generate README.md
        hook_list = "\n".join([f"- {hook}" for hook in hooks]) or "None"
        permission_list = "\n".join([f"- {perm}" for perm in permissions]) or "None"

        readme = README_TEMPLATE
        readme = readme.replace("{{name}}", name)
        readme = readme.replace("{{description}}", description)
        readme = readme.replace("{{author}}", author)
        readme = readme.replace("{{license}}", license)
        readme = readme.replace("{{usage}}", "TODO: Add usage instructions")
        readme = readme.replace("{{configuration}}", "TODO: Add configuration details")
        readme = readme.replace("{{hook_list}}", hook_list)
        readme = readme.replace("{{permission_list}}", permission_list)

        # Write README.md
        (output_dir / "README.md").write_text(readme)

        # Generate manifest.json
        manifest = MANIFEST_TEMPLATE
        manifest = manifest.replace("{{name}}", name)
        manifest = manifest.replace("{{version}}", version)
        manifest = manifest.replace("{{author}}", author)
        manifest = manifest.replace("{{description}}", description)
        manifest = manifest.replace("{{homepage}}", "")
        manifest = manifest.replace("{{repository}}", "")
        manifest = manifest.replace("{{license}}", license)
        manifest = manifest.replace("{{tags}}", json.dumps(tags))
        manifest = manifest.replace("{{hooks}}", json.dumps(hooks))
        manifest = manifest.replace("{{commands}}", json.dumps(commands))
        manifest = manifest.replace("{{permissions}}", json.dumps(permissions))

        # Write manifest.json
        (output_dir / "manifest.json").write_text(manifest)

        # Generate test file
        test_code = TEST_TEMPLATE
        test_code = test_code.replace("{{name}}", name)
        test_code = test_code.replace("{{class_name}}", class_name)
        test_code = test_code.replace("{{version}}", version)

        # Write test file
        (output_dir / "test_plugin.py").write_text(test_code)

        # Create __init__.py
        (output_dir / "__init__.py").write_text("")

        return output_dir

    def validate_plugin(self, plugin_dir: Path) -> Dict[str, Any]:
        """Validate a plugin directory structure and code.

        Args:
            plugin_dir: Plugin directory to validate

        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []

        # Check required files
        required_files = ["plugin.py", "manifest.json", "README.md"]
        for file_name in required_files:
            if not (plugin_dir / file_name).exists():
                errors.append(f"Missing required file: {file_name}")

        # Validate manifest.json
        manifest_file = plugin_dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file) as f:
                    manifest = json.load(f)

                # Check required fields
                required_fields = ["name", "version", "author", "description"]
                for field in required_fields:
                    if field not in manifest:
                        errors.append(f"Missing required field in manifest: {field}")

            except json.JSONDecodeError as e:
                errors.append(f"Invalid JSON in manifest: {e}")

        # Validate plugin.py
        plugin_file = plugin_dir / "plugin.py"
        if plugin_file.exists():
            try:
                code = plugin_file.read_text()

                # Check for Plugin class
                if "class" not in code or "Plugin" not in code:
                    errors.append("No Plugin class found in plugin.py")

                # Check for metadata property
                if "@property" not in code or "def metadata" not in code:
                    errors.append("No metadata property found in Plugin class")

                # Check for initialize method
                if "def initialize" not in code:
                    warnings.append("No initialize method found in Plugin class")

            except Exception as e:
                errors.append(f"Error reading plugin.py: {e}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def package_plugin(self, plugin_dir: Path, output_file: Optional[Path] = None) -> Path:
        """Package a plugin for distribution.

        Args:
            plugin_dir: Plugin directory
            output_file: Output file path (defaults to plugin_dir.tar.gz)

        Returns:
            Path to created package
        """
        import tarfile

        if not output_file:
            output_file = plugin_dir.parent / f"{plugin_dir.name}.tar.gz"

        with tarfile.open(output_file, "w:gz") as tar:
            tar.add(plugin_dir, arcname=plugin_dir.name)

        return output_file

    def test_plugin(self, plugin_dir: Path) -> bool:
        """Run tests for a plugin.

        Args:
            plugin_dir: Plugin directory

        Returns:
            True if tests pass
        """
        import subprocess

        test_file = plugin_dir / "test_plugin.py"
        if not test_file.exists():
            print("No test file found")
            return False

        try:
            result = subprocess.run(
                ["python", "-m", "unittest", str(test_file)],
                cwd=plugin_dir,
                capture_output=True,
                text=True,
            )

            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            return result.returncode == 0

        except Exception as e:
            print(f"Error running tests: {e}")
            return False

    def generate_docs(self, plugin_dir: Path) -> Path:
        """Generate documentation for a plugin.

        Args:
            plugin_dir: Plugin directory

        Returns:
            Path to generated docs
        """
        docs_dir = plugin_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        # Read manifest
        manifest_file = plugin_dir / "manifest.json"
        if not manifest_file.exists():
            raise ValueError("No manifest.json found")

        with open(manifest_file) as f:
            manifest = json.load(f)

        # Generate API documentation
        api_doc = f"""# {manifest['name']} API Documentation

## Metadata

- **Name**: {manifest['name']}
- **Version**: {manifest['version']}
- **Author**: {manifest['author']}
- **License**: {manifest.get('license', 'Unknown')}

## Description

{manifest['description']}

## Hooks

"""
        for hook in manifest.get('hooks', []):
            api_doc += f"- `{hook}`\n"

        api_doc += "\n## Commands\n\n"
        for cmd in manifest.get('commands', []):
            api_doc += f"- `{cmd}`\n"

        api_doc += "\n## Permissions\n\n"
        for perm in manifest.get('permissions', []):
            api_doc += f"- `{perm}`\n"

        # Write API doc
        api_doc_file = docs_dir / "API.md"
        api_doc_file.write_text(api_doc)

        return docs_dir
