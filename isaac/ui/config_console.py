"""
MVP Config Console for /mine settings
Provides a minimal TUI for tweaking collections search parameters during testing.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import TextArea, Checkbox, Button, Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import get_app
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.styles import Style


# Sandbox Settings Configuration
SANDBOX_SETTINGS = [
    {
        "key": "sandbox.enabled",
        "type": "bool",
        "default": False,
        "description": "Restrict Isaac to safe operations only"
    },
    {
        "key": "sandbox.root_dir",
        "type": "path",
        "default": "~/.isaac/sandboxes",
        "description": "Base directory for isolated environments"
    },
    {
        "key": "sandbox.block_system_paths",
        "type": "bool",
        "default": True,
        "description": "Prevent access to /etc, /sys, C:\\Windows, etc."
    },
    {
        "key": "sandbox.max_file_size_mb",
        "type": "int",
        "default": 100,
        "description": "Maximum file size for operations"
    },
    {
        "key": "sandbox.allowed_commands",
        "type": "list",
        "default": ["pip", "npm", "git", "python", "node"],
        "description": "Whitelist of allowed shell commands in sandbox"
    },
    {
        "key": "workspace.enabled",
        "type": "bool",
        "default": False,
        "description": "Enable workspace isolation and management"
    },
    {
        "key": "workspace.root_dir",
        "type": "path",
        "default": "~/.isaac/workspaces",
        "description": "Base directory for user workspaces"
    }
]


class ConfigConsole:
    """Minimal TUI for /mine settings configuration"""

    # Page definitions for future extensibility
    PAGES = {
        "main": {
            "title": "Isaac Configuration",
            "description": "Main configuration menu",
            "items": [
                {"type": "menu", "label": "Collections", "page": "collections", "description": "Search and collections settings"},
                {"type": "menu", "label": "Piping", "page": "piping", "description": "Output piping and context settings"},
                {"type": "menu", "label": "Sandbox", "page": "sandbox", "description": "Security and isolation settings"},
                {"type": "menu", "label": "Advanced", "page": "advanced", "description": "Advanced configuration options"},
                {"type": "menu", "label": "Workspaces", "page": "workspaces", "description": "Workspace and bot management"},
                {"type": "menu", "label": "System", "page": "system", "description": "System-wide settings"},
            ]
        },
        "collections": {"title": "Collections Settings", "parent": "main"},
        "piping": {"title": "Piping Settings", "parent": "main"},
        "sandbox": {"title": "Sandbox Settings", "parent": "main"},
        "advanced": {"title": "Advanced Settings", "parent": "main"},
        "workspaces": {"title": "Workspace Management", "parent": "main"},
        "system": {"title": "System Settings", "parent": "main"},
    }

    def __init__(self, session_manager=None):
        """Initialize config console with page system"""
        self.session_manager = session_manager
        self.config_file = Path.home() / '.isaac' / 'mine_config.json'
        self.sandbox_config_file = Path.home() / '.isaac' / 'config.json'
        self.settings = self._load_settings()
        self.sandbox_settings = self._load_sandbox_settings()
        self.saved = False
        self.cancelled = False
        self.status_text = "Use Tab to navigate, Enter to save, Esc to cancel"

        # Page navigation state
        self.current_page = "main"  # Start with main menu
        self.page_history = []  # For back navigation
        self.current_tab = "Collections"  # For backward compatibility

        # Focus management
        self.focusable_buttons = []  # List of focusable buttons in current layout
        self.focus_index = 0  # Current focused button index

        self._create_ui()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'max_chunk_size': 1000,
            'match_preview_length': 200,
            'multi_match_count': 5,
            'piping_threshold': 0.7,
            'piping_max_context': 3,
            'show_scores': True,
            'file_ids': [],  # List of file_ids to search within collections
            'search_files_only': False  # Whether to search only specific files
        }

    def _get_sandbox_defaults(self) -> Dict[str, Any]:
        """Get default sandbox settings"""
        defaults = {}
        for setting in SANDBOX_SETTINGS:
            defaults[setting["key"]] = setting["default"]
        return defaults

    def _load_sandbox_settings(self) -> Dict[str, Any]:
        """Load sandbox settings from config file"""
        defaults = self._get_sandbox_defaults()

        if self.sandbox_config_file.exists():
            try:
                with open(self.sandbox_config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge loaded settings with defaults
                    defaults.update(loaded)
            except Exception:
                pass  # Use defaults if file is corrupted

        return defaults

    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from config file"""
        defaults = self._get_defaults()

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge loaded settings with defaults
                    defaults.update(loaded)
            except Exception:
                pass  # Use defaults if file is corrupted

        return defaults

    def _save_sandbox_settings(self) -> bool:
        """Save current sandbox settings to config file"""
        try:
            # Ensure directory exists
            self.sandbox_config_file.parent.mkdir(parents=True, exist_ok=True)

            # Save settings
            with open(self.sandbox_config_file, 'w') as f:
                json.dump(self.sandbox_settings, f, indent=2)

            return True
        except Exception as e:
            self.status_text = f"Error saving sandbox config: {e}"
            return False

    def _create_ui(self):
        """Create the TUI interface"""

        # Check if we're on main menu or specific config page
        if self.current_page == "main":
            content_layout = self._create_main_menu_layout()
        else:
            # Initialize fields if navigating to config pages
            if not hasattr(self, 'max_chunk_size_field'):
                self._initialize_config_fields()
            # Use existing tab-based layout for config pages
            content_layout = self._create_tabbed_layout()

        # Create main container
        self.root_container = Frame(
            title="",
            body=content_layout
        )

        # Create application
        self.app = Application(
            layout=Layout(self.root_container),
            key_bindings=self._create_key_bindings(),
            style=self._create_style(),
            full_screen=False,
            erase_when_done=True
        )

    def _initialize_config_fields(self):
        """Initialize configuration fields for tabbed interface"""
        # This will be called when navigating to config pages
        # The fields are created in the individual layout methods
        pass

    def _create_tabbed_layout(self):
        """Create the traditional tabbed layout for config pages"""
        # ISAAC 2.0 ASCII Art Header - THE signature element
        header_text = """
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┳┏┓┏┓┏┓┏┓  ┏┓ ┏┓                                                            │
├─ ┃┗┓┣┫┣┫┃   ┏┛ ┃┃ ─────────────── ISAAC ──────────────── CONTROL CONSOLE ────┤
│  ┻┗┛┛┗┛┗┗┛  ┗━•┗┛                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
"""
        collections_tab = Button("[Collections]", handler=lambda: self._switch_tab("Collections"))
        piping_tab = Button("[Piping]", handler=lambda: self._switch_tab("Piping"))
        sandbox_tab = Button("[Sandbox]", handler=lambda: self._switch_tab("Sandbox"))
        advanced_tab = Button("[Advanced]", handler=lambda: self._switch_tab("Advanced"))

        # Highlight current tab
        if self.current_tab == "Collections":
            collections_tab.text = "[COLLECTIONS]"
        elif self.current_tab == "Piping":
            piping_tab.text = "[PIPING]"
        elif self.current_tab == "Sandbox":
            sandbox_tab.text = "[SANDBOX]"
        elif self.current_tab == "Advanced":
            advanced_tab.text = "[ADVANCED]"

        # Create tab bar
        tab_bar = VSplit([
            collections_tab,
            Window(width=1),
            piping_tab,
            Window(width=1),
            sandbox_tab,
            Window(width=1),
            advanced_tab
        ], height=1)

        # Create content based on current tab
        if self.current_tab == "Collections":
            content_layout = self._create_collections_layout()
        elif self.current_tab == "Piping":
            content_layout = self._create_piping_layout()
        elif self.current_tab == "Sandbox":
            content_layout = self._create_sandbox_layout()
        else:  # Advanced
            content_layout = self._create_advanced_layout()

        # Layout - Fixed width for consistent display
        header_window = Window(
            content=FormattedTextControl(header_text.strip()),
            height=len(header_text.split('\n')),
            width=80,  # Fixed width
            dont_extend_width=True
        )

        # Main layout
        main_layout = HSplit([
            header_window,
            Window(height=1),  # Spacing
            tab_bar,
            Window(content=FormattedTextControl(""), height=1),  # Separator
            content_layout
        ])

        # Create main container with fixed width
        self.root_container = Frame(
            title="",
            body=main_layout
        )

        # Create application
        self.app = Application(
            layout=Layout(self.root_container),
            key_bindings=self._create_key_bindings(),
            style=self._create_style(),
            full_screen=False,
            erase_when_done=True
        )

    def _navigate_to_page(self, page_name: str):
        """Navigate to a different page"""
        if page_name in self.PAGES:
            self.page_history.append(self.current_page)
            self.current_page = page_name

            # Map page to tab for backward compatibility
            page_to_tab = {
                "collections": "Collections",
                "piping": "Piping",
                "sandbox": "Sandbox",
                "advanced": "Advanced",
                "workspaces": "Workspaces"
            }
            if page_name in page_to_tab:
                self.current_tab = page_to_tab[page_name]
            elif page_name == "main":
                self.current_tab = "Collections"  # Default

            # Update layout without recreating app
            self._update_layout()
            if hasattr(self, 'app'):
                self.app.invalidate()

    def _update_layout(self):
        """Update the layout without recreating the application"""
        # Check if we're on main menu or specific config page
        if self.current_page == "main":
            content_layout = self._create_main_menu_layout()
        elif self.current_page == "workspaces":
            content_layout = self._create_workspaces_layout()
        else:
            # Initialize fields if navigating to config pages
            if not hasattr(self, 'max_chunk_size_field'):
                # Create a dummy layout to initialize fields
                self._create_collections_layout()
            # Use existing tab-based layout for config pages
            content_layout = self._create_tabbed_layout()

        # Update the root container
        self.root_container = Frame(
            title="",
            body=content_layout
        )

        # Update app layout if it exists
        if hasattr(self, 'app'):
            self.app.layout = Layout(self.root_container)

    def _navigate_back(self):
        """Navigate back to previous page"""
        if self.page_history:
            self.current_page = self.page_history.pop()
            self._create_ui()
            if hasattr(self, 'app'):
                self.app.invalidate()

    def _create_main_menu_layout(self):
        """Create the main menu layout"""
        page_info = self.PAGES[self.current_page]

        # Header
        header_text = f"""
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┳┏┓┏┓┏┓┏┓  ┏┓ ┏┓                                                            │
├─ ┃┗┓┣┫┣┫┃   ┏┛ ┃┃ ─────────────── ISAAC ──────────────── CONFIGURATION ──────┤
│  ┻┗┛┛┗┛┗┗┛  ┗━•┗┛                                                            │
└──────────────────────────────────────────────────────────────────────────────┘

{page_info['title']}
{page_info.get('description', '')}
"""

        # Reset focusable buttons for this layout
        self.focusable_buttons = []

        # Create menu items - just buttons for now to test focus
        menu_buttons = []
        for item in page_info.get('items', []):
            if item['type'] == 'menu':
                # Create a button for menu navigation
                button = Button(f"  {item['label']} - {item['description']}", handler=lambda x=item: self._navigate_to_page(x['page']))
                self.focusable_buttons.append(button)
                menu_buttons.append(button)

        # Navigation buttons
        back_button = Button("Back", handler=self._navigate_back) if self.page_history else None
        exit_button = Button("Exit", handler=lambda: setattr(self, 'cancelled', True) or self.app.exit())
        
        # Add navigation buttons to focusable list
        if back_button:
            self.focusable_buttons.append(back_button)
        self.focusable_buttons.append(exit_button)

        # Layout
        layout_items = [
            Window(content=FormattedTextControl(header_text.strip()), height=len(header_text.split('\n')), width=80, dont_extend_width=True),
            Window(height=1),  # Spacing
        ]

        # Add menu items
        for item in menu_buttons:
            layout_items.append(item)
            layout_items.append(Window(height=1))  # Spacing between items

        # Add navigation buttons at bottom
        button_row = [Window(width=2)]  # Left padding
        if back_button:
            button_row.extend([back_button, Window(width=2)])
        button_row.extend([exit_button])

        layout_items.extend([
            Window(height=2),  # Spacing before buttons
            VSplit(button_row),
            Window(height=1)  # Bottom spacing
        ])

        return HSplit(layout_items)

    def _switch_tab(self, tab_name: str):
        """Switch to a different tab"""
        self.current_tab = tab_name
        self._create_ui()  # Recreate UI with new tab
        # Force redraw
        if hasattr(self, 'app'):
            self.app.invalidate()

    def _create_collections_layout(self):
        """Create the Collections tab layout"""
        # Settings fields with pale background styling
        self.max_chunk_size_field = TextArea(
            text=str(self.settings['max_chunk_size']),
            multiline=False,
            height=1,
            width=10,
            style='class:input-field'
        )

        self.match_preview_length_field = TextArea(
            text=str(self.settings['match_preview_length']),
            multiline=False,
            height=1,
            width=10,
            style='class:input-field'
        )

        self.multi_match_count_field = TextArea(
            text=str(self.settings['multi_match_count']),
            multiline=False,
            height=1,
            width=10,
            style='class:input-field'
        )

        self.show_scores_checkbox = Checkbox(
            text="Show match scores",
            checked=self.settings['show_scores']
        )

        self.search_files_only_checkbox = Checkbox(
            text="Search only specific files",
            checked=self.settings['search_files_only']
        )

        self.file_ids_field = TextArea(
            text='\n'.join(self.settings['file_ids']),
            multiline=True,     
            height=5,
            width=70,
            style='class:input-field'
        )

        # Status and buttons
        save_button = Button("Save", handler=self._handle_save)
        cancel_button = Button("Cancel", handler=self._handle_cancel)

        return HSplit([
            Window(height=1),  # Spacing

            # Output Settings Section
            Window(content=FormattedTextControl("  Output Settings:"), height=1, width=76),

            # Max Chunk Size
            VSplit([
                Window(content=FormattedTextControl("    max_chunk_size:       "), width=28, dont_extend_width=True),
                self.max_chunk_size_field,
                Window(content=FormattedTextControl(" chars (single match output)"), width=35, dont_extend_width=True)
            ]),

            # Match Preview Length
            VSplit([
                Window(content=FormattedTextControl("    match_preview_length: "), width=28, dont_extend_width=True),
                self.match_preview_length_field,
                Window(content=FormattedTextControl(" chars (preview per match)"), width=35, dont_extend_width=True)
            ]),

            # Multi Match Count
            VSplit([
                Window(content=FormattedTextControl("    multi_match_count:    "), width=28, dont_extend_width=True),
                self.multi_match_count_field,
                Window(content=FormattedTextControl(" matches (how many to show)"), width=35, dont_extend_width=True)
            ]),

            Window(height=1),  # Spacing

            # Display Options Section
            Window(content=FormattedTextControl("  Display Options:"), height=1, width=76),

            # Show Scores
            VSplit([
                Window(content=FormattedTextControl("    "), width=4, dont_extend_width=True),
                self.show_scores_checkbox,
                Window(content=FormattedTextControl("    Show relevance scores with matches"), width=45, dont_extend_width=True)
            ]),

            # Search Files Only
            VSplit([
                Window(content=FormattedTextControl("    "), width=4, dont_extend_width=True),
                self.search_files_only_checkbox,
                Window(content=FormattedTextControl("    Search only specific files"), width=45, dont_extend_width=True)
            ]),

            Window(height=1),  # Spacing

            # File IDs Section
            Window(content=FormattedTextControl("  File IDs (one per line):"), height=1, width=76),
            VSplit([
                Window(content=FormattedTextControl("    "), width=4, dont_extend_width=True),
                self.file_ids_field,
                Window(width=1)
            ]),

            Window(height=2),  # Spacing

            # Status
            Window(content=FormattedTextControl(lambda: "  " + self.status_text), height=2, width=76),

            # Buttons
            VSplit([
                Window(width=30),  # Left padding for centering
                save_button,
                Window(width=2),
                cancel_button
            ]),

            Window(height=1)  # Bottom spacing
        ])

    def _create_piping_layout(self):
        """Create the Piping tab layout"""
        # Piping-specific fields
        self.piping_threshold_field = TextArea(
            text=str(self.settings.get('piping_threshold', 0.7)),
            multiline=False,
            height=1,
            width=10,
            style='class:input-field'
        )

        self.piping_max_context_field = TextArea(
            text=str(self.settings.get('piping_max_context', 3)),
            multiline=False,
            height=1,
            width=10,
            style='class:input-field'
        )

        save_button = Button("Save", handler=self._handle_save)
        cancel_button = Button("Cancel", handler=self._handle_cancel)

        return HSplit([
            Window(height=1),  # Spacing

            # Piping Settings Section
            Window(content=FormattedTextControl("  Piping Settings:"), height=1, width=76),

            # Piping Threshold
            VSplit([
                Window(content=FormattedTextControl("    piping_threshold:     "), width=28, dont_extend_width=True),
                self.piping_threshold_field,
                Window(content=FormattedTextControl(" chars (when /ask truncates)"), width=35, dont_extend_width=True)
            ]),

            # Piping Max Context
            VSplit([
                Window(content=FormattedTextControl("    piping_max_context:   "), width=28, dont_extend_width=True),
                self.piping_max_context_field,
                Window(content=FormattedTextControl(" chars (max context to /ask)"), width=35, dont_extend_width=True)
            ]),

            Window(height=10),  # Fill space

            # Status
            Window(content=FormattedTextControl(lambda: "  " + self.status_text), height=2, width=76),

            # Buttons
            VSplit([
                Window(width=30),  # Left padding for centering
                save_button,
                Window(width=2),
                cancel_button
            ]),

            Window(height=1)  # Bottom spacing
        ])

    def _create_sandbox_layout(self):
        """Create the Sandbox tab layout"""
        # Sandbox fields
        self.sandbox_enabled_checkbox = Checkbox(
            text="Enable Sandbox Mode",
            checked=self.sandbox_settings.get('sandbox.enabled', False)
        )

        self.sandbox_root_dir_field = TextArea(
            text=str(self.sandbox_settings.get('sandbox.root_dir', '~/.isaac/sandboxes')),
            multiline=False,
            height=1,
            width=50,
            style='class:input-field'
        )

        self.sandbox_block_system_checkbox = Checkbox(
            text="Block System Directories",
            checked=self.sandbox_settings.get('sandbox.block_system_paths', True)
        )

        self.sandbox_max_file_size_field = TextArea(
            text=str(self.sandbox_settings.get('sandbox.max_file_size_mb', 100)),
            multiline=False,
            height=1,
            width=10,
            style='class:input-field'
        )

        self.sandbox_allowed_commands_field = TextArea(
            text=', '.join(self.sandbox_settings.get('sandbox.allowed_commands', ['pip', 'npm', 'git', 'python', 'node'])),
            multiline=False,
            height=1,
            width=50,
            style='class:input-field'
        )

        save_button = Button("Save", handler=self._handle_save)
        cancel_button = Button("Cancel", handler=self._handle_cancel)

        return HSplit([
            Window(height=1),  # Spacing

            # Sandbox Settings Section
            Window(content=FormattedTextControl("  Sandbox Settings:"), height=1, width=76),

            Window(height=1),  # Spacing

            # Enable Sandbox Mode
            VSplit([
                Window(content=FormattedTextControl("    "), width=4, dont_extend_width=True),
                self.sandbox_enabled_checkbox,
                Window(content=FormattedTextControl("    Restrict Isaac to safe operations only"), width=45, dont_extend_width=True)
            ]),

            Window(height=1),  # Spacing

            # Sandbox Root Directory
            VSplit([
                Window(content=FormattedTextControl("    Root Directory:       "), width=28, dont_extend_width=True),
                self.sandbox_root_dir_field,
                Window(width=1)
            ]),

            Window(height=1),  # Spacing

            # Block System Directories
            VSplit([
                Window(content=FormattedTextControl("    "), width=4, dont_extend_width=True),
                self.sandbox_block_system_checkbox,
                Window(content=FormattedTextControl("    Prevent access to /etc, /sys, C:\\Windows, etc."), width=50, dont_extend_width=True)
            ]),

            Window(height=1),  # Spacing

            # Max File Size
            VSplit([
                Window(content=FormattedTextControl("    Max File Size (MB):   "), width=28, dont_extend_width=True),
                self.sandbox_max_file_size_field,
                Window(content=FormattedTextControl(" MB (maximum file size for operations)"), width=35, dont_extend_width=True)
            ]),

            Window(height=1),  # Spacing

            # Allowed Commands
            Window(content=FormattedTextControl("    Allowed Commands:"), height=1, width=76),
            VSplit([
                Window(content=FormattedTextControl("      "), width=6, dont_extend_width=True),
                self.sandbox_allowed_commands_field,
                Window(width=1)
            ]),

            Window(height=5),  # Fill space

            # Warning
            Window(content=FormattedTextControl("  ⚠ Sandbox mode restricts dangerous operations"), height=1, width=76),

            Window(height=2),  # Spacing

            # Status
            Window(content=FormattedTextControl(lambda: "  " + self.status_text), height=2, width=76),

            # Buttons
            VSplit([
                Window(width=30),  # Left padding for centering
                save_button,
                Window(width=2),
                cancel_button
            ]),

            Window(height=1)  # Bottom spacing
        ])

    def _create_advanced_layout(self):
        """Create the Advanced tab layout"""
        save_button = Button("Save", handler=self._handle_save)
        cancel_button = Button("Cancel", handler=self._handle_cancel)

        return HSplit([
            Window(height=1),  # Spacing

            # Advanced Settings Section
            Window(content=FormattedTextControl("  Advanced Settings:"), height=1, width=76),

            Window(height=1),  # Spacing

            Window(content=FormattedTextControl("    [Advanced settings coming soon]"), height=1, width=76),

            Window(height=15),  # Fill space

            # Status
            Window(content=FormattedTextControl(lambda: "  " + self.status_text), height=2, width=76),

            # Buttons
            VSplit([
                Window(width=30),  # Left padding for centering
                save_button,
                Window(width=2),
                cancel_button
            ]),

            Window(height=1)  # Bottom spacing
        ])

    def _create_workspaces_layout(self):
        """Create the Workspaces management layout"""
        # Get current workspace settings
        workspace_enabled = self.session_manager.get_config("workspace.enabled", False)
        workspace_root = self.session_manager.get_config("workspace.root_dir", "~/.isaac/workspaces")

        # Create checkboxes and fields
        self.workspace_enabled_checkbox = Checkbox(
            text="Enable workspace isolation and management",
            checked=workspace_enabled
        )

        self.workspace_root_dir_field = TextArea(
            text=workspace_root,
            multiline=False,
            height=1,
            width=50,
            style='class:input-field'
        )

        # Status and buttons
        save_button = Button("Save", handler=self._handle_save)
        cancel_button = Button("Cancel", handler=self._handle_cancel)

        # Create workspace list display
        workspace_list_text = "No workspaces found."
        if workspace_enabled:
            try:
                from isaac.core.sandbox_enforcer import SandboxEnforcer
                enforcer = SandboxEnforcer(self.session_manager)
                workspaces = enforcer.list_workspaces()
                if workspaces:
                    workspace_list_text = "Current workspaces:\n" + "\n".join(f"  • {ws}" for ws in workspaces)
                else:
                    workspace_list_text = "No workspaces found. Create one with 'isaac workspace create <name>'"
            except Exception as e:
                workspace_list_text = f"Error listing workspaces: {e}"

        return HSplit([
            Window(height=1),  # Spacing

            # Workspace Settings Section
            Window(content=FormattedTextControl("  Workspace Settings:"), height=1, width=76),

            # Enable Workspace Isolation
            VSplit([
                Window(content=FormattedTextControl("    "), width=4, dont_extend_width=True),
                self.workspace_enabled_checkbox,
                Window(width=1)
            ]),

            Window(height=1),  # Spacing

            # Workspace Root Directory
            VSplit([
                Window(content=FormattedTextControl("    Root Directory: "), width=20, dont_extend_width=True),
                self.workspace_root_dir_field,
                Window(width=1)
            ]),

            Window(height=2),  # Spacing

            # Current Workspaces Section
            Window(content=FormattedTextControl("  Current Workspaces:"), height=1, width=76),
            Window(content=FormattedTextControl(f"    {workspace_list_text}"), height=5, width=76),

            Window(height=2),  # Spacing

            # Commands Section
            Window(content=FormattedTextControl("  Available Commands:"), height=1, width=76),
            Window(content=FormattedTextControl("    isaac workspace create <name>  - Create new workspace"), height=1, width=76),
            Window(content=FormattedTextControl("    isaac workspace list           - List all workspaces"), height=1, width=76),
            Window(content=FormattedTextControl("    isaac workspace switch <name>  - Switch to workspace"), height=1, width=76),
            Window(content=FormattedTextControl("    isaac workspace delete <name>  - Delete workspace"), height=1, width=76),

            Window(height=5),  # Fill space

            # Status
            Window(content=FormattedTextControl(lambda: "  " + self.status_text), height=2, width=76),

            # Buttons
            VSplit([
                Window(width=30),  # Left padding for centering
                save_button,
                Window(width=2),
                cancel_button
            ]),

            Window(height=1)  # Bottom spacing
        ])

    def _handle_save(self):
        """Handle save button click"""
        # Update settings from UI fields
        if self.current_tab == "Collections":
            self._update_collections_settings()
        elif self.current_tab == "Piping":
            self._update_piping_settings()
        elif self.current_tab == "Sandbox":
            self._update_sandbox_settings()
        elif self.current_tab == "Workspaces":
            self._update_workspace_settings()

        # Validate and save
        error = self._validate_current_tab()
        if error:
            self.status_text = f"Error: {error}"
            return

        # Save settings
        if self.current_tab in ["Collections", "Piping"]:
            success = self._save_settings()
        elif self.current_tab in ["Sandbox", "Workspaces"]:
            success = self._save_sandbox_settings()
        else:
            success = True

        if success:
            self.saved = True
            self.status_text = "Settings saved successfully!"
        else:
            self.status_text = "Failed to save settings"

    def _handle_cancel(self):
        """Handle cancel button click"""
        self.cancelled = True
        self.status_text = "Changes cancelled"

    def _update_collections_settings(self):
        """Update collections settings from UI fields"""
        self.settings['max_chunk_size'] = int(self.max_chunk_size_field.text)
        self.settings['match_preview_length'] = int(self.match_preview_length_field.text)
        self.settings['multi_match_count'] = int(self.multi_match_count_field.text)
        self.settings['show_scores'] = self.show_scores_checkbox.checked
        self.settings['search_files_only'] = self.search_files_only_checkbox.checked
        self.settings['file_ids'] = [line.strip() for line in self.file_ids_field.text.split('\n') if line.strip()]

    def _update_piping_settings(self):
        """Update piping settings from UI fields"""
        self.settings['piping_threshold'] = float(self.piping_threshold_field.text)
        self.settings['piping_max_context'] = int(self.piping_max_context_field.text)

    def _update_sandbox_settings(self):
        """Update sandbox settings from UI fields"""
        self.sandbox_settings['sandbox.enabled'] = self.sandbox_enabled_checkbox.checked
        self.sandbox_settings['sandbox.root_dir'] = self.sandbox_root_dir_field.text
        self.sandbox_settings['sandbox.block_system_paths'] = self.sandbox_block_system_checkbox.checked
        self.sandbox_settings['sandbox.max_file_size_mb'] = int(self.sandbox_max_file_size_field.text)
        self.sandbox_settings['sandbox.allowed_commands'] = [
            cmd.strip() for cmd in self.sandbox_allowed_commands_field.text.split(',') if cmd.strip()
        ]

    def _update_workspace_settings(self):
        """Update workspace settings from UI fields"""
        self.sandbox_settings['workspace.enabled'] = self.workspace_enabled_checkbox.checked
        self.sandbox_settings['workspace.root_dir'] = self.workspace_root_dir_field.text

    def _validate_current_tab(self) -> Optional[str]:
        """Validate settings for current tab"""
        if self.current_tab == "Collections":
            return self._validate_collections_settings()
        elif self.current_tab == "Piping":
            return self._validate_piping_settings()
        elif self.current_tab == "Sandbox":
            return self._validate_sandbox_settings()
        elif self.current_tab == "Workspaces":
            return self._validate_workspace_settings()
        return None

    def _validate_collections_settings(self) -> Optional[str]:
        """Validate collections settings"""
        try:
            if int(self.max_chunk_size_field.text) <= 0:
                return "Max Chunk Size must be positive"
        except ValueError:
            return "Max Chunk Size must be a valid integer"

        try:
            if int(self.match_preview_length_field.text) <= 0:
                return "Match Preview Length must be positive"
        except ValueError:
            return "Match Preview Length must be a valid integer"

        try:
            if int(self.multi_match_count_field.text) <= 0:
                return "Multi Match Count must be positive"
        except ValueError:
            return "Multi Match Count must be a valid integer"

        return None

    def _validate_piping_settings(self) -> Optional[str]:
        """Validate piping settings"""
        try:
            threshold = float(self.piping_threshold_field.text)
            if not 0 <= threshold <= 1:
                return "Piping Threshold must be between 0 and 1"
        except ValueError:
            return "Piping Threshold must be a valid number"

        try:
            if int(self.piping_max_context_field.text) <= 0:
                return "Piping Max Context must be positive"
        except ValueError:
            return "Piping Max Context must be a valid integer"

        return None

    def _validate_sandbox_settings(self) -> Optional[str]:
        """Validate sandbox settings"""
        try:
            if int(self.sandbox_max_file_size_field.text) <= 0:
                return "Max File Size must be positive"
        except ValueError:
            return "Max File Size must be a valid integer"

        return None

    def _validate_workspace_settings(self) -> Optional[str]:
        """Validate workspace settings"""
        # Validate workspace root directory path
        root_dir = self.workspace_root_dir_field.text.strip()
        if not root_dir:
            return "Workspace root directory cannot be empty"

        # Basic path validation (could be enhanced)
        if ".." in root_dir:
            return "Workspace root directory cannot contain '..'"

        return None

    def _create_key_bindings(self):
        """Create key bindings for the application"""
        kb = KeyBindings()

        # Use built-in focus navigation
        kb.add('tab')(focus_next)
        kb.add('s-tab')(focus_previous)  # Shift+Tab

        @kb.add('space')
        def _(event):
            # Activate the currently focused button
            app = get_app()
            if app.layout.current_control and hasattr(app.layout.current_control, 'handler'):
                if app.layout.current_control.handler:
                    app.layout.current_control.handler()

        @kb.add('backspace')
        def _(event):
            # Navigate back to previous page
            if self.current_page != "main":
                self._navigate_back()

        @kb.add('enter')
        def _(event):
            # Activate the currently focused button
            app = get_app()
            if app.layout.current_control and hasattr(app.layout.current_control, 'handler'):
                if app.layout.current_control.handler:
                    app.layout.current_control.handler()

        @kb.add('escape')
        def _(event):
            if self.current_page != "main":
                self._navigate_back()
            else:
                self._handle_cancel()
                get_app().exit()

        return kb

    def _tab_next_field(self):
        """Navigate to next field in current tab"""
        # This would need to be implemented based on current tab
        # For now, just focus save button
        pass

    def _create_style(self):
        """Create the application style"""
        return Style([
            ('input-field', 'bg:#f0f0f0 #000000'),
            ('button', 'bg:#008000 #ffffff'),
            ('button.focused', 'bg:#00ff00 #000000'),
            ('checkbox', '#000000'),
            ('checkbox.checked', 'bg:#008000 #ffffff'),
        ])

    def run(self):
        """Run the configuration console"""
        try:
            self.app.run()
            return self.saved
        except Exception as e:
            print(f"Error running config console: {e}")
            return False


def show_config_console(session_manager=None) -> str:
    """Entry point for the config console command"""
    console = ConfigConsole(session_manager)

    try:
        saved = console.run()
        if saved:
            return "✓ /mine settings updated successfully"
        else:
            return "✗ /mine settings not saved"
    except Exception as e:
        return f"✗ Error running config console: {e}"              