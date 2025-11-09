"""Plugin command - Manage Isaac plugins."""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

from isaac.plugins import PluginManager, PluginRegistry
from isaac.plugins.plugin_devkit import PluginDevKit


class PluginCommand:
    """Manage Isaac plugins: install, remove, enable, disable, and more."""

    def __init__(self):
        """Initialize plugin command."""
        self.manager = PluginManager()
        self.registry = PluginRegistry()
        self.devkit = PluginDevKit()

    def execute(self, args: List[str]) -> int:
        """Execute the plugin command.

        Args:
            args: Command arguments

        Returns:
            Exit code (0 for success)
        """
        if not args or args[0] in ["--help", "-h"]:
            self._show_help()
            return 0

        subcommand = args[0]
        subargs = args[1:]

        subcommands = {
            "install": self._install,
            "uninstall": self._uninstall,
            "remove": self._uninstall,  # Alias
            "enable": self._enable,
            "disable": self._disable,
            "list": self._list,
            "ls": self._list,  # Alias
            "search": self._search,
            "info": self._info,
            "update": self._update,
            "featured": self._featured,
            "create": self._create,
            "validate": self._validate,
            "test": self._test,
            "package": self._package,
        }

        if subcommand in subcommands:
            try:
                return subcommands[subcommand](subargs)
            except Exception as e:
                print(f"Error: {e}")
                return 1
        else:
            print(f"Unknown subcommand: {subcommand}")
            print("Run 'plugin --help' for usage information")
            return 1

    def _show_help(self) -> None:
        """Show help message."""
        help_text = """
Plugin Management - Install, manage, and develop Isaac plugins

USAGE:
    plugin <subcommand> [options]

SUBCOMMANDS:
    install <name>          Install a plugin from the registry
    uninstall <name>        Uninstall a plugin
    enable <name>           Enable a disabled plugin
    disable <name>          Disable a plugin
    list                    List installed plugins
    search <query>          Search for plugins in the registry
    info <name>             Show detailed information about a plugin
    update [name]           Update a plugin (or all plugins)
    featured                Show featured plugins

    Developer Commands:
    create <name>           Create a new plugin from template
    validate <path>         Validate a plugin directory
    test <path>             Run tests for a plugin
    package <path>          Package a plugin for distribution

OPTIONS:
    --help, -h             Show this help message
    --force, -f            Force operation (for install/update)
    --all, -a              Apply to all plugins (for update)

EXAMPLES:
    # Install a plugin
    plugin install command-logger

    # Search for plugins
    plugin search git

    # List installed plugins
    plugin list

    # Create a new plugin
    plugin create my-plugin

    # Update all plugins
    plugin update --all

For more information, visit: https://isaac.dev/docs/plugins
"""
        print(help_text)

    def _install(self, args: List[str]) -> int:
        """Install a plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin name required")
            print("Usage: plugin install <name> [--force]")
            return 1

        name = args[0]
        force = "--force" in args or "-f" in args

        print(f"Installing plugin: {name}")
        success = self.manager.install(name, force=force)

        return 0 if success else 1

    def _uninstall(self, args: List[str]) -> int:
        """Uninstall a plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin name required")
            print("Usage: plugin uninstall <name>")
            return 1

        name = args[0]

        print(f"Uninstalling plugin: {name}")
        success = self.manager.uninstall(name)

        return 0 if success else 1

    def _enable(self, args: List[str]) -> int:
        """Enable a plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin name required")
            print("Usage: plugin enable <name>")
            return 1

        name = args[0]
        success = self.manager.enable(name)

        return 0 if success else 1

    def _disable(self, args: List[str]) -> int:
        """Disable a plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin name required")
            print("Usage: plugin disable <name>")
            return 1

        name = args[0]
        success = self.manager.disable(name)

        return 0 if success else 1

    def _list(self, args: List[str]) -> int:
        """List installed plugins.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        plugins = self.manager.list_installed()

        if not plugins:
            print("No plugins installed")
            return 0

        print("\nInstalled Plugins:")
        print("-" * 80)

        for metadata in plugins:
            status = "✓ enabled" if metadata.enabled else "✗ disabled"
            print(f"\n{metadata.name} ({metadata.version}) - {status}")
            print(f"  {metadata.description}")
            print(f"  Author: {metadata.author}")

            if metadata.tags:
                print(f"  Tags: {', '.join(metadata.tags)}")

            if metadata.install_date:
                install_date = metadata.install_date.strftime("%Y-%m-%d")
                print(f"  Installed: {install_date}")

        print()
        return 0

    def _search(self, args: List[str]) -> int:
        """Search for plugins.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        query = " ".join(args) if args else None

        if not query:
            print("Usage: plugin search <query>")
            print("Example: plugin search git")
            return 1

        print(f"Searching for: {query}")
        print()

        # Update registry
        self.registry.update()

        # Search
        results = self.registry.search(query=query)

        if not results:
            print("No plugins found")
            return 0

        print(f"Found {len(results)} plugin(s):")
        print("-" * 80)

        for entry in results[:10]:  # Show top 10
            metadata = entry.metadata
            badges = []

            if entry.featured:
                badges.append("⭐ FEATURED")
            if entry.verified:
                badges.append("✓ VERIFIED")

            badge_str = " ".join(badges) if badges else ""

            print(f"\n{metadata.name} ({metadata.version}) {badge_str}")
            print(f"  {metadata.description}")
            print(f"  Downloads: {entry.downloads} | Rating: {entry.rating:.1f}/5.0")

            if metadata.tags:
                print(f"  Tags: {', '.join(metadata.tags[:5])}")

        print()
        return 0

    def _info(self, args: List[str]) -> int:
        """Show plugin information.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin name required")
            print("Usage: plugin info <name>")
            return 1

        name = args[0]

        # Check if installed
        metadata = self.manager.get_metadata(name)
        if metadata:
            self._show_installed_info(metadata)
            return 0

        # Check registry
        entry = self.registry.get(name)
        if entry:
            self._show_registry_info(entry)
            return 0

        print(f"Plugin not found: {name}")
        return 1

    def _show_installed_info(self, metadata) -> None:
        """Show information for installed plugin."""
        print(f"\n{metadata.name} ({metadata.version})")
        print("=" * 80)
        print(f"\nStatus: {'Enabled' if metadata.enabled else 'Disabled'}")
        print(f"Author: {metadata.author}")
        print(f"License: {metadata.license}")
        print(f"\nDescription:")
        print(f"  {metadata.description}")

        if metadata.tags:
            print(f"\nTags: {', '.join(metadata.tags)}")

        if metadata.hooks:
            print(f"\nHooks:")
            for hook in metadata.hooks:
                print(f"  - {hook.value}")

        if metadata.commands:
            print(f"\nCommands:")
            for cmd in metadata.commands:
                print(f"  - {cmd}")

        if metadata.permissions:
            print(f"\nPermissions:")
            for perm in metadata.permissions:
                print(f"  - {perm}")

        if metadata.install_date:
            print(f"\nInstalled: {metadata.install_date.strftime('%Y-%m-%d %H:%M:%S')}")

        print()

    def _show_registry_info(self, entry) -> None:
        """Show information for registry plugin."""
        metadata = entry.metadata

        badges = []
        if entry.featured:
            badges.append("⭐ FEATURED")
        if entry.verified:
            badges.append("✓ VERIFIED")

        badge_str = " " + " ".join(badges) if badges else ""

        print(f"\n{metadata.name} ({metadata.version}){badge_str}")
        print("=" * 80)
        print(f"\nAuthor: {metadata.author}")
        print(f"License: {metadata.license}")
        print(f"\nDescription:")
        print(f"  {metadata.description}")

        if metadata.homepage:
            print(f"\nHomepage: {metadata.homepage}")

        if metadata.repository:
            print(f"Repository: {metadata.repository}")

        print(f"\nStatistics:")
        print(f"  Downloads: {entry.downloads}")
        print(f"  Rating: {entry.rating:.1f}/5.0 ({entry.reviews} reviews)")

        if metadata.tags:
            print(f"\nTags: {', '.join(metadata.tags)}")

        if metadata.hooks:
            print(f"\nHooks: {', '.join(h.value for h in metadata.hooks)}")

        if metadata.permissions:
            print(f"\nRequired Permissions:")
            for perm in metadata.permissions:
                print(f"  - {perm}")

        print(f"\nTo install: plugin install {metadata.name}")
        print()

    def _update(self, args: List[str]) -> int:
        """Update plugin(s).

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        update_all = "--all" in args or "-a" in args

        if update_all:
            print("Updating all plugins...")
            results = self.manager.update_all()

            success_count = sum(1 for r in results.values() if r)
            print(f"\nUpdated {success_count}/{len(results)} plugins")

            return 0 if success_count > 0 else 1

        elif args:
            name = args[0]
            success = self.manager.update(name)
            return 0 if success else 1

        else:
            print("Usage: plugin update <name> OR plugin update --all")
            return 1

    def _featured(self, args: List[str]) -> int:
        """Show featured plugins.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        print("Featured Plugins:")
        print("-" * 80)

        # Update registry
        self.registry.update()

        # Get featured plugins
        featured = self.registry.list_featured()

        if not featured:
            print("No featured plugins available")
            return 0

        for entry in featured:
            metadata = entry.metadata
            installed = self.manager.get_metadata(metadata.name) is not None
            status = " [INSTALLED]" if installed else ""

            print(f"\n⭐ {metadata.name} ({metadata.version}){status}")
            print(f"   {metadata.description}")
            print(f"   Downloads: {entry.downloads} | Rating: {entry.rating:.1f}/5.0")

        print()
        return 0

    def _create(self, args: List[str]) -> int:
        """Create a new plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin name required")
            print("Usage: plugin create <name>")
            return 1

        name = args[0]

        # Interactive prompts
        print(f"Creating plugin: {name}")
        print()

        author = input("Author name: ").strip() or "Unknown"
        description = input("Description: ").strip() or "A new Isaac plugin"

        # Ask for hooks
        print("\nAvailable hooks:")
        print("1. startup        - Plugin initialization")
        print("2. shutdown       - Plugin cleanup")
        print("3. before_command - Before command execution")
        print("4. after_command  - After command execution")
        print("5. file_changed   - When files change")
        print()

        hooks_input = input("Enter hook numbers (comma-separated, or press Enter to skip): ").strip()
        hooks = []
        if hooks_input:
            hook_map = {
                "1": "STARTUP",
                "2": "SHUTDOWN",
                "3": "BEFORE_COMMAND",
                "4": "AFTER_COMMAND",
                "5": "FILE_CHANGED",
            }
            for num in hooks_input.split(","):
                num = num.strip()
                if num in hook_map:
                    hooks.append(hook_map[num])

        # Create plugin
        plugin_dir = self.devkit.create_plugin(
            name=name,
            author=author,
            description=description,
            hooks=hooks,
        )

        print(f"\n✓ Plugin created: {plugin_dir}")
        print(f"\nNext steps:")
        print(f"1. Edit {plugin_dir}/plugin.py to implement your plugin")
        print(f"2. Test with: plugin test {plugin_dir}")
        print(f"3. Install with: plugin install {name}")

        return 0

    def _validate(self, args: List[str]) -> int:
        """Validate a plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin path required")
            print("Usage: plugin validate <path>")
            return 1

        plugin_dir = Path(args[0])
        if not plugin_dir.exists():
            print(f"Error: Directory not found: {plugin_dir}")
            return 1

        print(f"Validating plugin: {plugin_dir}")
        print()

        result = self.devkit.validate_plugin(plugin_dir)

        if result["errors"]:
            print("✗ Validation failed:")
            for error in result["errors"]:
                print(f"  - {error}")

        if result["warnings"]:
            print("\n⚠ Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")

        if result["valid"]:
            print("\n✓ Plugin is valid")
            return 0
        else:
            return 1

    def _test(self, args: List[str]) -> int:
        """Run plugin tests.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin path required")
            print("Usage: plugin test <path>")
            return 1

        plugin_dir = Path(args[0])
        if not plugin_dir.exists():
            print(f"Error: Directory not found: {plugin_dir}")
            return 1

        print(f"Running tests for: {plugin_dir}")
        print()

        success = self.devkit.test_plugin(plugin_dir)
        return 0 if success else 1

    def _package(self, args: List[str]) -> int:
        """Package a plugin.

        Args:
            args: Command arguments

        Returns:
            Exit code
        """
        if not args:
            print("Error: Plugin path required")
            print("Usage: plugin package <path>")
            return 1

        plugin_dir = Path(args[0])
        if not plugin_dir.exists():
            print(f"Error: Directory not found: {plugin_dir}")
            return 1

        print(f"Packaging plugin: {plugin_dir}")

        try:
            package_file = self.devkit.package_plugin(plugin_dir)
            print(f"✓ Package created: {package_file}")
            return 0
        except Exception as e:
            print(f"✗ Packaging failed: {e}")
            return 1
