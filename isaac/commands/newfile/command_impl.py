"""
Newfile Command - Standardized Implementation

Create files with templates and proper path handling.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.core.session_manager import SessionManager


class NewfileCommand(BaseCommand):
    """Create files with templates and proper path handling"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute newfile command.

        Args:
            args: Command arguments
            context: Optional execution context (includes piped_input for stdin content)

        Returns:
            CommandResponse with file creation result
        """
        parser = FlagParser(args)

        # Check for help
        if parser.has_flag('help', ['h']):
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        # Get session manager
        session_manager = SessionManager()

        # Check for list templates
        if parser.has_flag('list-templates', ['l']):
            return self._handle_list_templates(session_manager)

        # Check for set template
        if parser.has_flag('set-template', ['s']):
            ext = parser.get_flag('set-template')
            # In FlagParser, we need to get the next positional args for extension and content
            # For now, let's handle this differently
            positional = parser.get_all_positional()
            if len(positional) >= 2:
                ext = positional[0]
                content = positional[1]
                return self._handle_set_template(session_manager, ext, content)
            else:
                return CommandResponse(
                    success=False,
                    error="--set-template requires extension and content",
                    metadata={"error_code": "MISSING_ARGUMENT"}
                )

        # Get filename
        filename = parser.get_positional(0)

        if not filename:
            return CommandResponse(
                success=True,
                data=self.get_help()
            )

        # Get options
        template = parser.get_flag('template', aliases=['t'])
        content = parser.get_flag('content', aliases=['c'])
        force = parser.has_flag('force', ['f'])

        # Check for piped content
        if content is None and context and "piped_input" in context:
            content = context["piped_input"]

        return self._handle_create_file(session_manager, filename, template, content, force)

    def _handle_list_templates(self, session_manager: SessionManager) -> CommandResponse:
        """List available templates"""
        templates = self._get_templates(session_manager)

        if not templates:
            return CommandResponse(
                success=True,
                data="No templates available",
                metadata={"count": 0}
            )

        output = "Available templates:\n\n"
        for ext in sorted(templates.keys()):
            items = templates[ext]
            if isinstance(items, list) and items and isinstance(items[0], dict):
                desc = items[0].get("desc", "") or "(no description)"
                output += f"  {ext:<8} → {desc}\n"
            else:
                output += f"  {ext:<8} → (invalid template)\n"

        output += "\nUse /newfile <file> --template <ext> to use a template"

        return CommandResponse(
            success=True,
            data=output,
            metadata={"count": len(templates)}
        )

    def _handle_set_template(self, session_manager: SessionManager, ext: str, content: str) -> CommandResponse:
        """Set template for extension"""
        # Normalize extension
        if not ext.startswith("."):
            ext = f".{ext}"

        templates = self._get_templates(session_manager)
        templates[ext.lower()] = [{"desc": f"Custom template for {ext}", "body": content}]

        # Save to session
        config = session_manager.get_config()
        config["newfile_templates"] = templates
        session_manager._save_config()

        return CommandResponse(
            success=True,
            data=f"Template set for {ext}",
            metadata={"extension": ext}
        )

    def _handle_create_file(
        self,
        session_manager: SessionManager,
        filename: str,
        template: Optional[str],
        content: Optional[str],
        force: bool
    ) -> CommandResponse:
        """Create a new file"""
        try:
            # Strip surrounding quotes if present
            filename = filename.strip('"').strip("'")

            # Expand path properly
            filepath = Path(filename).expanduser().resolve()

            # Create parent directories if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # Check if file exists
            if filepath.exists() and not force:
                return CommandResponse(
                    success=False,
                    error=f"File {filepath} exists. Use --force to overwrite.",
                    metadata={"error_code": "FILE_EXISTS"}
                )

            # Get content
            file_content = ""
            if content:
                # Inline content provided
                file_content = content
            elif template:
                # Use template
                templates = self._get_templates(session_manager)
                template_content = self._get_template_content(templates, template, filepath.suffix)
                if template_content:
                    file_content = template_content
            else:
                # Use default template for extension
                templates = self._get_templates(session_manager)
                template_content = self._get_template_content(templates, filepath.suffix, filepath.suffix)
                if template_content:
                    file_content = template_content

            # Write file
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_content)

            return CommandResponse(
                success=True,
                data=f"File created: {filepath}",
                metadata={
                    "file_path": str(filepath),
                    "bytes_written": len(file_content)
                }
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Error creating file: {e}",
                metadata={"error_code": "CREATE_FAILED"}
            )

    def _get_templates(self, session_manager: SessionManager) -> Dict[str, Any]:
        """Get templates from session config"""
        config = session_manager.get_config()
        templates = config.get("newfile_templates", self._get_default_templates())

        # Validate that templates is a dict with proper structure
        if not isinstance(templates, dict):
            return self._get_default_templates()

        # Clean invalid entries
        cleaned = {}
        for ext, items in templates.items():
            if isinstance(items, list) and items and isinstance(items[0], dict):
                cleaned[ext] = items

        # Merge with defaults for missing extensions
        defaults = self._get_default_templates()
        for ext, items in defaults.items():
            if ext not in cleaned:
                cleaned[ext] = items

        return cleaned

    def _get_default_templates(self) -> Dict[str, Any]:
        """Get default templates"""
        return {
            ".py": [
                {
                    "desc": "Python starter",
                    "body": "#!/usr/bin/env python\nif __name__=='__main__':\n    print('hello')\n",
                }
            ],
            ".txt": [{"desc": "Plain notes", "body": "# Notes\n"}],
            ".md": [{"desc": "Markdown doc", "body": "# Markdown Document\n"}],
            ".json": [{"desc": "Basic JSON", "body": '{\n  "name": "new_project"\n}\n'}],
            ".html": [
                {
                    "desc": "HTML skeleton",
                    "body": '<!DOCTYPE html>\n<html>\n<head>\n  <meta charset="utf-8" />\n  <title>New File</title>\n</head>\n<body>\n</body>\n</html>\n',
                }
            ],
        }

    def _get_template_content(
        self, templates: Dict[str, Any], template_spec: str, file_ext: str
    ) -> Optional[str]:
        """Get template content for given spec"""
        # Try exact extension match first
        ext_key = template_spec.lower()
        if not ext_key.startswith("."):
            ext_key = f".{ext_key}"

        if ext_key in templates:
            items = templates[ext_key]
            if isinstance(items, list) and items and isinstance(items[0], dict):
                return items[0].get("body", "")

        # Try file extension match
        file_ext_key = file_ext.lower()
        if file_ext_key in templates:
            items = templates[file_ext_key]
            if isinstance(items, list) and items and isinstance(items[0], dict):
                return items[0].get("body", "")

        return None

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="newfile",
            description="Create files with templates and proper path handling",
            usage="/newfile <file> [--template EXT] [--content TEXT] [--force]",
            examples=[
                "/newfile script.py  # Create Python file with starter code",
                "/newfile notes.txt --content \"My notes\"  # Create with custom content",
                "/newfile report.md --template .md  # Use Markdown template",
                "/newfile --list-templates  # Show available templates",
                "echo \"content\" | /newfile output.txt  # Create from piped input"
            ],
            tier=2,  # Needs validation - creates files
            aliases=["nf", "touch"],
            category="file"
        )
