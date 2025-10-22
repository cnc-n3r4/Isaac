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
from prompt_toolkit.layout.containers import WindowAlign
from prompt_toolkit.application import get_app
import asyncio


class ConfigConsole:
    """Minimal TUI for /mine settings configuration"""

    def __init__(self, session_manager=None):
        self.session_manager = session_manager
        self.config_file = Path.home() / '.isaac' / 'mine_config.json'
        self.settings = self._load_settings()
        self.saved = False
        self.cancelled = False
        self.status_text = "Use Tab to navigate, Enter to save, Esc to cancel"
        self._create_ui()

    def _get_defaults(self) -> Dict[str, Any]:
        """Get default settings"""
        return {
            'max_chunk_size': 1000,
            'match_preview_length': 200,
            'multi_match_count': 5,
            'piping_threshold': 0.7,
            'piping_max_context': 3,
            'show_scores': True
        }

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

    def _save_settings(self) -> bool:
        """Save current settings to config file"""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            # Save settings
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            return True
        except Exception as e:
            self.status_text = f"Error saving config: {e}"
            return False

    def _create_ui(self):
        """Create the TUI interface"""

        # ASCII Art Header
        header_text = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                           ISAAC /mine CONFIG CONSOLE                       ║
║                                                                            ║
║  Configure collections search parameters for optimal performance          ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

        # Settings fields
        self.max_chunk_size_field = TextArea(
            text=str(self.settings['max_chunk_size']),
            multiline=False,
            height=1,
            width=10
        )

        self.match_preview_length_field = TextArea(
            text=str(self.settings['match_preview_length']),
            multiline=False,
            height=1,
            width=10
        )

        self.multi_match_count_field = TextArea(
            text=str(self.settings['multi_match_count']),
            multiline=False,
            height=1,
            width=10
        )

        self.piping_threshold_field = TextArea(
            text=str(self.settings['piping_threshold']),
            multiline=False,
            height=1,
            width=10
        )

        self.piping_max_context_field = TextArea(
            text=str(self.settings['piping_max_context']),
            multiline=False,
            height=1,
            width=10
        )

        self.show_scores_checkbox = Checkbox(
            text="Show match scores",
            checked=self.settings['show_scores']
        )

        # Status and buttons
        save_button = Button("Save", handler=self._handle_save)
        cancel_button = Button("Cancel", handler=self._handle_cancel)

        # Layout
        header_window = Window(
            content=FormattedTextControl(header_text.strip()),
            height=len(header_text.split('\n')),
            align=WindowAlign.CENTER
        )

        settings_layout = HSplit([
            # Max Chunk Size
            VSplit([
                Window(content=FormattedTextControl("Max Chunk Size: "), width=20),
                self.max_chunk_size_field,
                Window(content=FormattedTextControl("  Maximum characters per chunk"), width=35)
            ]),

            # Match Preview Length
            VSplit([
                Window(content=FormattedTextControl("Match Preview Length: "), width=25),
                self.match_preview_length_field,
                Window(content=FormattedTextControl("  Characters to show in preview"), width=35)
            ]),

            # Multi Match Count
            VSplit([
                Window(content=FormattedTextControl("Multi Match Count: "), width=20),
                self.multi_match_count_field,
                Window(content=FormattedTextControl("  Max matches per collection"), width=35)
            ]),

            # Piping Threshold
            VSplit([
                Window(content=FormattedTextControl("Piping Threshold: "), width=18),
                self.piping_threshold_field,
                Window(content=FormattedTextControl("  Min similarity for piping (0.0-1.0)"), width=40)
            ]),

            # Piping Max Context
            VSplit([
                Window(content=FormattedTextControl("Piping Max Context: "), width=20),
                self.piping_max_context_field,
                Window(content=FormattedTextControl("  Context lines for piping"), width=35)
            ]),

            # Show Scores
            VSplit([
                Window(content=FormattedTextControl(""), width=20),
                self.show_scores_checkbox,
                Window(content=FormattedTextControl("  Display similarity scores"), width=35)
            ]),

            # Status
            Window(content=FormattedTextControl(lambda: self.status_text), height=2),

            # Buttons
            VSplit([
                save_button,
                cancel_button
            ], padding=2)
        ])

        self.layout = Layout(HSplit([
            header_window,
            Frame(settings_layout, title="Collections Settings")
        ]))

        # Key bindings
        self.kb = KeyBindings()

        @self.kb.add('tab')
        def _(event):
            # Tab navigation between fields
            current_focus = get_app().layout.current_window
            if current_focus == self.max_chunk_size_field.window:
                get_app().layout.focus(self.match_preview_length_field.window)
            elif current_focus == self.match_preview_length_field.window:
                get_app().layout.focus(self.multi_match_count_field.window)
            elif current_focus == self.multi_match_count_field.window:
                get_app().layout.focus(self.piping_threshold_field.window)
            elif current_focus == self.piping_threshold_field.window:
                get_app().layout.focus(self.piping_max_context_field.window)
            elif current_focus == self.piping_max_context_field.window:
                get_app().layout.focus(self.show_scores_checkbox.window)
            else:
                get_app().layout.focus(self.max_chunk_size_field.window)

        @self.kb.add('enter')
        def _(event):
            self._handle_save()
            get_app().exit()

        @self.kb.add('escape')
        def _(event):
            self._handle_cancel()
            get_app().exit()

    def _validate_settings(self) -> Optional[str]:
        """Validate all settings and return error message if invalid"""
        try:
            max_chunk_size = int(self.max_chunk_size_field.text)
            if max_chunk_size <= 0:
                return "Max Chunk Size must be positive"
            self.settings['max_chunk_size'] = max_chunk_size
        except ValueError:
            return "Max Chunk Size must be a valid integer"

        try:
            match_preview_length = int(self.match_preview_length_field.text)
            if match_preview_length <= 0:
                return "Match Preview Length must be positive"
            self.settings['match_preview_length'] = match_preview_length
        except ValueError:
            return "Match Preview Length must be a valid integer"

        try:
            multi_match_count = int(self.multi_match_count_field.text)
            if multi_match_count <= 0:
                return "Multi Match Count must be positive"
            self.settings['multi_match_count'] = multi_match_count
        except ValueError:
            return "Multi Match Count must be a valid integer"

        try:
            piping_threshold = float(self.piping_threshold_field.text)
            if not 0.0 <= piping_threshold <= 1.0:
                return "Piping Threshold must be between 0.0 and 1.0"
            self.settings['piping_threshold'] = piping_threshold
        except ValueError:
            return "Piping Threshold must be a valid number"

        try:
            piping_max_context = int(self.piping_max_context_field.text)
            if piping_max_context < 0:
                return "Piping Max Context must be non-negative"
            self.settings['piping_max_context'] = piping_max_context
        except ValueError:
            return "Piping Max Context must be a valid integer"

        self.settings['show_scores'] = self.show_scores_checkbox.checked

        return None  # No errors

    def _handle_save(self):
        """Handle save button click"""
        error = self._validate_settings()
        if error:
            self.status_text = f"Validation Error: {error}"
            return

        if self._save_settings():
            self.status_text = "Settings saved successfully!"
            self.saved = True
        else:
            self.status_text = "Failed to save settings. Check file permissions."

    def _handle_cancel(self):
        """Handle cancel button click"""
        self.status_text = "Changes cancelled."
        self.cancelled = True

    def run(self) -> bool:
        """Run the config console and return True if settings were saved"""
        self.saved = False
        self.cancelled = False

        # Set up asyncio event loop for Windows compatibility
        try:
            # Try to use asyncio event loop policy for better Windows support
            import asyncio
            # Try different event loop policies for Windows compatibility
            for policy_name in ['WindowsSelectorEventLoopPolicy', 'WindowsProactorEventLoopPolicy']:
                if hasattr(asyncio, policy_name):
                    policy_class = getattr(asyncio, policy_name)
                    asyncio.set_event_loop_policy(policy_class())
                    break
        except (AttributeError, ImportError, RuntimeError):
            # Event loop policy setting failed, continue with defaults
            pass

        try:
            app = Application(
                layout=self.layout,
                key_bindings=self.kb,
                full_screen=True,
                # Use standard input/output for better Windows compatibility
                input=None,
                output=None
            )

            # Initial focus
            app.layout.focus(self.max_chunk_size_field.window)

            app.run()
        except KeyboardInterrupt:
            self.cancelled = True
        except Exception as e:
            # If prompt_toolkit fails for any reason, fall back to text interface
            print(f"Warning: TUI not available ({e}), using text interface...")
            return self._run_text_fallback()

        return self.saved and not self.cancelled

    def _run_text_fallback(self) -> bool:
        """Run a simple text-based fallback interface"""
        # Check if we're in an interactive context
        import sys
        try:
            # Try to peek at stdin to see if there's input available
            import select
            if hasattr(sys.stdin, 'fileno'):
                # On Unix-like systems
                ready, _, _ = select.select([sys.stdin], [], [], 0)
                if not ready:
                    # No input available, not interactive
                    return self._run_non_interactive_fallback()
        except (ImportError, AttributeError, OSError):
            # select not available or stdin not suitable, assume non-interactive
            return self._run_non_interactive_fallback()
        
        print("\n=== ISAAC /mine CONFIG CONSOLE (Text Mode) ===")
        print("Configure collections search parameters\n")

        # Display current settings
        print("Current settings:")
        for key, value in self.settings.items():
            print(f"  {key}: {value}")
        print()

        # Simple text-based editing
        print("Enter new values (press Enter to keep current, 'q' to quit):")

        new_settings = self.settings.copy()

        # Get user input for each setting
        prompts = {
            'max_chunk_size': 'Max Chunk Size (current: {}): ',
            'match_preview_length': 'Match Preview Length (current: {}): ',
            'multi_match_count': 'Multi Match Count (current: {}): ',
            'piping_threshold': 'Piping Threshold (current: {}): ',
            'piping_max_context': 'Piping Max Context (current: {}): ',
            'show_scores': 'Show Scores (true/false, current: {}): '
        }

        for key, prompt in prompts.items():
            try:
                current = new_settings[key]
                user_input = input(prompt.format(current)).strip()

                if user_input.lower() == 'q':
                    print("Cancelled.")
                    return False

                if user_input:  # Only update if user entered something
                    if key == 'show_scores':
                        new_settings[key] = user_input.lower() in ['true', '1', 'yes', 'y']
                    elif isinstance(current, int):
                        new_settings[key] = int(user_input)
                    elif isinstance(current, float):
                        new_settings[key] = float(user_input)
                    else:
                        new_settings[key] = user_input

            except (ValueError, KeyboardInterrupt):
                print(f"Invalid input for {key}, keeping current value.")
                continue

        # Validate settings
        error = self._validate_settings_from_dict(new_settings)
        if error:
            print(f"Validation error: {error}")
            return False

        # Save settings
        self.settings = new_settings
        if self._save_settings():
            print("Settings saved successfully!")
            return True
        else:
            print("Failed to save settings.")
            return False

    def _run_non_interactive_fallback(self) -> bool:
        """Handle non-interactive execution (e.g., from dispatcher)"""
        # In non-interactive mode, just show current settings
        output_lines = [
            "=== ISAAC /mine CONFIG CONSOLE (Non-Interactive) ===",
            "Configure collections search parameters",
            "",
            "Current settings:"
        ]
        
        for key, value in self.settings.items():
            output_lines.append(f"  {key}: {value}")
        
        output_lines.extend([
            "",
            "Note: Use interactive mode for configuration changes.",
            "Settings loaded successfully."
        ])
        
        print("\n".join(output_lines))
        return True

    def _validate_settings_from_dict(self, settings_dict: Dict[str, Any]) -> Optional[str]:
        """Validate settings from a dictionary"""
        try:
            if settings_dict['max_chunk_size'] <= 0:
                return "Max Chunk Size must be positive"
        except (KeyError, TypeError):
            return "Invalid max_chunk_size"

        try:
            if settings_dict['match_preview_length'] <= 0:
                return "Match Preview Length must be positive"
        except (KeyError, TypeError):
            return "Invalid match_preview_length"

        try:
            if settings_dict['multi_match_count'] <= 0:
                return "Multi Match Count must be positive"
        except (KeyError, TypeError):
            return "Invalid multi_match_count"

        try:
            if not 0.0 <= settings_dict['piping_threshold'] <= 1.0:
                return "Piping Threshold must be between 0.0 and 1.0"
        except (KeyError, TypeError):
            return "Invalid piping_threshold"

        try:
            if settings_dict['piping_max_context'] < 0:
                return "Piping Max Context must be non-negative"
        except (KeyError, TypeError):
            return "Invalid piping_max_context"

        return None  # No errors


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