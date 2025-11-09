#!/usr/bin/env python3
"""
ISAAC Man Page System
Generates Unix-style manual pages from command metadata
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ManPageGenerator:
    """
    Generate Unix-style man pages from command.yaml metadata

    Provides:
    - Full manual pages (/man command)
    - Keyword search (/apropos keyword)
    - Quick reference (/whatis command)
    """

    def __init__(self, commands_dir: Optional[Path] = None):
        """
        Initialize man page generator

        Args:
            commands_dir: Path to commands directory
        """
        if commands_dir is None:
            isaac_root = Path(__file__).parent.parent
            commands_dir = isaac_root / "commands"

        self.commands_dir = commands_dir
        self.commands: Dict[str, Dict[str, Any]] = {}
        self._load_commands()

    def _load_commands(self):
        """Load all command metadata"""
        if not self.commands_dir.exists():
            return

        for item in self.commands_dir.iterdir():
            if not item.is_dir() or item.name.startswith(("_", ".")):
                continue

            yaml_file = item / "command.yaml"
            if not yaml_file.exists():
                continue

            try:
                with open(yaml_file, "r") as f:
                    metadata = yaml.safe_load(f)
                    if metadata:
                        self.commands[item.name] = metadata
            except Exception:
                pass

    def get_man_page(self, command: str) -> Optional[str]:
        """
        Generate full man page for a command

        Args:
            command: Command name (with or without /)

        Returns:
            Formatted man page or None if not found
        """
        # Remove leading slash if present
        cmd_name = command.lstrip("/")

        # Check if command exists
        if cmd_name not in self.commands:
            # Try to find by trigger
            for name, metadata in self.commands.items():
                triggers = metadata.get("triggers", [])
                if f"/{cmd_name}" in triggers or command in triggers:
                    cmd_name = name
                    break
            else:
                return None

        metadata = self.commands[cmd_name]
        return self._format_man_page(cmd_name, metadata)

    def _format_man_page(self, name: str, meta: Dict[str, Any]) -> str:
        """Format a man page from metadata"""
        lines = []

        # Header
        version = meta.get("version", "1.0.0")
        trigger = meta.get("triggers", [f"/{name}"])[0]

        lines.append(f"{trigger.upper()}({version})".center(70))
        lines.append("")

        # NAME section
        lines.append("NAME")
        summary = meta.get("summary", "No description")
        lines.append(f"    {trigger} - {summary}")
        lines.append("")

        # SYNOPSIS section
        lines.append("SYNOPSIS")
        synopsis = self._generate_synopsis(trigger, meta)
        for line in synopsis:
            lines.append(f"    {line}")
        lines.append("")

        # DESCRIPTION section
        description = meta.get("description", summary)
        if description:
            lines.append("DESCRIPTION")
            # Format description with indentation
            for line in description.strip().split("\n"):
                if line.strip():
                    lines.append(f"    {line}")
                else:
                    lines.append("")
            lines.append("")

        # OPTIONS section
        args = meta.get("args", [])
        if args:
            lines.append("OPTIONS")
            for arg in args:
                arg_name = arg.get("name", "arg")
                arg_help = arg.get("help", "")
                arg_required = arg.get("required", False)
                arg_enum = arg.get("enum", [])

                if arg_required:
                    lines.append(f"    --{arg_name} <value>  (required)")
                else:
                    lines.append(f"    --{arg_name} [value]")

                if arg_help:
                    lines.append(f"        {arg_help}")

                if arg_enum:
                    enum_str = ", ".join(arg_enum)
                    lines.append(f"        Choices: {enum_str}")

                lines.append("")

        # EXAMPLES section
        examples = meta.get("examples", [])
        if examples:
            lines.append("EXAMPLES")
            for example in examples:
                # Remove comments from example
                example_clean = example.split("#")[0].strip()
                comment = example.split("#")[1].strip() if "#" in example else ""

                lines.append(f"    {example_clean}")
                if comment:
                    lines.append(f"        # {comment}")
            lines.append("")

        # ALIASES section
        aliases = meta.get("aliases", [])
        if aliases:
            lines.append("ALIASES")
            alias_str = ", ".join(aliases)
            lines.append(f"    {alias_str}")
            lines.append("")

        # DEPENDENCIES section
        deps = meta.get("dependencies", {})
        if deps.get("api_keys") or deps.get("packages"):
            lines.append("DEPENDENCIES")
            if deps.get("api_keys"):
                lines.append("    API Keys:")
                for key in deps["api_keys"]:
                    lines.append(f"        {key}")
            if deps.get("packages"):
                lines.append("    Python Packages:")
                for pkg in deps["packages"]:
                    lines.append(f"        {pkg}")
            lines.append("")

        # STATUS section
        status = meta.get("status", "stable")
        if status != "stable":
            lines.append("STATUS")
            lines.append(f"    {status.upper()}")
            stub_reason = meta.get("stub_reason")
            if stub_reason:
                lines.append(f"    {stub_reason}")
            lines.append("")

        # SEE ALSO section
        lines.append("SEE ALSO")
        lines.append(f"    /help {trigger}")
        lines.append(f"    /apropos {name}")
        lines.append("")

        # Footer
        lines.append("━" * 70)
        lines.append(f"ISAAC v2.0.0".center(70))
        lines.append(f"{name} version {version}".center(70))

        return "\n".join(lines)

    def _generate_synopsis(self, trigger: str, meta: Dict[str, Any]) -> List[str]:
        """Generate synopsis lines"""
        lines = [trigger]

        args = meta.get("args", [])
        for arg in args:
            arg_name = arg.get("name", "arg")
            if arg.get("required"):
                lines.append(f"    --{arg_name} <value>")
            else:
                lines.append(f"    [--{arg_name} <value>]")

        return lines

    def search(self, keyword: str) -> List[Dict[str, str]]:
        """
        Search commands by keyword (apropos)

        Args:
            keyword: Search term

        Returns:
            List of matching commands with name, trigger, and summary
        """
        keyword_lower = keyword.lower()
        results = []

        for name, metadata in self.commands.items():
            # Search in name, summary, description, and tags
            searchable = [
                name,
                metadata.get("summary", ""),
                metadata.get("description", ""),
                " ".join(metadata.get("triggers", [])),
                " ".join(metadata.get("aliases", [])),
            ]

            searchable_text = " ".join(searchable).lower()

            if keyword_lower in searchable_text:
                trigger = metadata.get("triggers", [f"/{name}"])[0]
                summary = metadata.get("summary", "No description")

                results.append(
                    {
                        "name": name,
                        "trigger": trigger,
                        "summary": summary,
                        "version": metadata.get("version", "1.0.0"),
                    }
                )

        return sorted(results, key=lambda x: x["name"])

    def whatis(self, command: str) -> Optional[str]:
        """
        Get one-line summary (whatis)

        Args:
            command: Command name

        Returns:
            One-line summary or None
        """
        cmd_name = command.lstrip("/")

        if cmd_name not in self.commands:
            # Try triggers
            for name, metadata in self.commands.items():
                triggers = metadata.get("triggers", [])
                if f"/{cmd_name}" in triggers or command in triggers:
                    cmd_name = name
                    break
            else:
                return None

        metadata = self.commands[cmd_name]
        trigger = metadata.get("triggers", [f"/{cmd_name}"])[0]
        summary = metadata.get("summary", "No description")
        version = metadata.get("version", "1.0.0")

        return f"{trigger} ({version}) - {summary}"

    def get_all_commands(self) -> List[Dict[str, str]]:
        """Get list of all commands with summaries"""
        results = []

        for name, metadata in sorted(self.commands.items()):
            trigger = metadata.get("triggers", [f"/{name}"])[0]
            summary = metadata.get("summary", "No description")
            version = metadata.get("version", "1.0.0")

            results.append(
                {"name": name, "trigger": trigger, "summary": summary, "version": version}
            )

        return results


# Singleton instance
_generator = None


def get_generator() -> ManPageGenerator:
    """Get or create man page generator instance"""
    global _generator
    if _generator is None:
        _generator = ManPageGenerator()
    return _generator
