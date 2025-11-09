"""Hello World Plugin - A simple example plugin.

This plugin demonstrates the basic structure of an Isaac plugin.
"""

from isaac.plugins.plugin_api import Plugin, PluginMetadata, PluginContext, PluginHook


class HelloWorldPlugin(Plugin):
    """Simple hello world plugin."""

    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name="hello-world",
            version="1.0.0",
            author="Isaac Team",
            description="A simple hello world plugin that demonstrates basic plugin functionality",
            license="MIT",
            tags=["example", "demo", "tutorial"],
            hooks=[PluginHook.STARTUP, PluginHook.BEFORE_COMMAND],
            commands=[],
            permissions=[],
        )

    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin.

        Args:
            context: Plugin context
        """
        self._context = context

        # Register hooks
        self.register_hook(PluginHook.STARTUP, self.on_startup)
        self.register_hook(PluginHook.BEFORE_COMMAND, self.on_before_command)

        print(f"[HelloWorld] Plugin initialized in workspace: {context.workspace_path}")

    def shutdown(self) -> None:
        """Clean up plugin resources."""
        print("[HelloWorld] Plugin shutting down. Goodbye!")

    def on_startup(self) -> None:
        """Handle startup hook."""
        print("[HelloWorld] Isaac is starting up!")
        print("[HelloWorld] Hello from the plugin system!")

    def on_before_command(self) -> None:
        """Handle before_command hook."""
        if self._context:
            command = self._context.event_data.get("command", "")
            if command:
                print(f"[HelloWorld] About to execute: {command}")
