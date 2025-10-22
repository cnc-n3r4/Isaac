# MVP Config Console - Phase 1 Spec

## Goal

Create minimal TUI config console for tweaking `/mine` settings during testing. Focus on **function over features** - just enough to iterate quickly.

## User Story

```powershell
# Testing piping behavior
isaac> /mine dig coolant | /ask what is this?
[Output truncated too much]

# Quick tweak
isaac> /config console
[TUI opens - single screen, Collections settings only]
[Tab through fields, change numbers, Save]
[Returns to shell]

# Test again
isaac> /mine dig coolant | /ask what is this?
[Better output with new settings]
```

## UI Design - Single Screen Only

**Signature Element:** The ISAAC 2.0 ASCII art header - this is what makes the config console distinct and cool.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┳┏┓┏┓┏┓┏┓  ┏┓ ┏┓                                                            │
├─ ┃┗┓┣┫┣┫┃   ┏┛ ┃┃ ─────────────── COLLECTIONS ───────────── CONTROL CONSOLE ─┤
│  ┻┗┛┛┗┛┗┗┛  ┗━•┗┛                                                            │
│                                                                              │
│   Output Settings:                                                           │
│     max_chunk_size:       [2000    ] chars (single match output)             │
│     match_preview_length: [500     ] chars (preview per match)               │
│     multi_match_count:    [3       ] matches (how many to show)              │
│                                                                              │
│   Piping Settings:                                                           │
│     piping_threshold:     [10000   ] chars (when /ask truncates)             │
│     piping_max_context:   [8000    ] chars (max context to /ask)             │
│                                                                              │
│   Display Options:                                                           │
│     [✓] show_scores       Show relevance scores with matches                 │
│                                                                              │
│                                                                              │
│   Current Active Collection: cnc-info (4 documents)                          │
│                                                                              │
│                                                                              │
│     < COLLECTIONS >  < AI >  < CLOUD >  < GENERAL >                          │
│                                                                              │
│                                                 < SAVE > < CANCEL >          │
│                                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Controls

**Navigation:**
- `Tab` - Next field
- `Shift+Tab` - Previous field
- `↑/↓` - Navigate fields (alternative to Tab)

**Editing:**
- `Enter` - Edit focused field (numeric input)
- `Space` - Toggle checkbox
- `Type digits` - Update number
- `Backspace/Delete` - Edit number
- `Esc` - Cancel edit, restore original value

**Actions:**
- `Tab to SAVE` + `Enter` - Save and close
- `Tab to CANCEL` + `Enter` - Cancel and close
- `Esc` anywhere - Cancel and close (same as CANCEL button)

## Fields

**All numeric fields:**
1. `max_chunk_size` - Integer, range 100-50000, default 2000
2. `match_preview_length` - Integer, range 50-10000, default 500
3. `multi_match_count` - Integer, range 1-10, default 3
4. `piping_threshold` - Integer, range 1000-100000, default 10000
5. `piping_max_context` - Integer, range 1000-50000, default 8000

**Checkbox:**
6. `show_scores` - Boolean, default True

## Validation

**Real-time validation as user types:**
- Min/max range enforcement
- Non-negative integers only
- Invalid input = field turns red
- Can't save while any field is invalid

**Example:**
```
max_chunk_size: [-500  ]  ← Red border, error message
                ^^^^^^^^
                Must be between 100-50000
```

## Data Flow

**On Open:**
1. Read current config from `~/.isaac/config.json`
2. Load values from `config['mine']` section
3. If section missing, use defaults
4. Display in form

**On Save:**
1. Validate all fields
2. Update `session.config['mine']` with new values
3. Write to `~/.isaac/config.json`
4. Close TUI
5. Return to shell

**On Cancel:**
1. Discard all changes
2. Close TUI
3. Return to shell

## Border Characters & Header Art

Using Unicode box-drawing characters for clean borders and the **signature ISAAC 2.0 ASCII art**:

```python
# Border characters (Unicode box-drawing)
TOP_LEFT = '┌'
TOP_RIGHT = '┐'
BOTTOM_LEFT = '└'
BOTTOM_RIGHT = '┘'
HORIZONTAL = '─'
VERTICAL = '│'
T_DOWN = '┬'
T_UP = '┴'
T_RIGHT = '├'
T_LEFT = '┤'

# ISAAC 2.0 ASCII art (THE signature header - this is what makes it cool!)
ISAAC_ASCII = [
    "┳┏┓┏┓┏┓┏┓  ┏┓ ┏┓",
    "┃┗┓┣┫┣┫┃   ┏┛ ┃┃",
    "┻┗┛┛┗┛┗┗┛  ┗━•┗┛"
]

# Header divider line with title
def create_header_line(title: str, subtitle: str = "CONTROL CONSOLE") -> str:
    """
    Creates the styled header divider:
    ├─ ┃┗┓┣┫┣┫┃   ┏┛ ┃┃ ─────────── COLLECTIONS ───────────── CONTROL CONSOLE ─┤
    """
    # Calculate padding for centered title
    total_width = 78  # Inner width (80 - 2 for borders)
    ascii_width = len(ISAAC_ASCII[1])  # Width of middle ASCII line
    
    # Build: ├─ [ASCII] ─── [TITLE] ─── [SUBTITLE] ─┤
    left_part = f"├─ {ISAAC_ASCII[1]} "
    right_part = f" {subtitle} ─┤"
    remaining = total_width - len(left_part) - len(right_part) - len(title)
    
    left_dashes = '─' * (remaining // 2)
    right_dashes = '─' * (remaining - len(left_dashes))
    
    return f"{left_part}{left_dashes} {title} {right_dashes}{right_part}"
```

**Why the ISAAC ASCII art is cool:**
- Unique visual identity for the config console
- Consistent branding with the splash screen
- Makes it feel like "Isaac's control panel" not just a generic form
- The `┗━•` gives it character (literally a bullet point after ISAAC)

## Implementation - `prompt_toolkit` Approach

```python
# isaac/ui/config_console.py

from prompt_toolkit.application import Application
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window, FormattedTextControl
from prompt_toolkit.widgets import Button, CheckBox, TextArea, Label, Frame
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
import json
from pathlib import Path

class ConfigConsole:
    """Minimal TUI config console for /mine settings."""
    
    def __init__(self, session_manager):
        self.session = session_manager
        self.original_config = self._load_mine_config()
        self.fields = self._create_fields()
        
    def _load_mine_config(self) -> dict:
        """Load current mine config with defaults."""
        defaults = {
            'max_chunk_size': 2000,
            'match_preview_length': 500,
            'multi_match_count': 3,
            'piping_threshold': 10000,
            'piping_max_context': 8000,
            'show_scores': True
        }
        mine_config = self.session.config.get('mine', {})
        return {**defaults, **mine_config}
    
    def _create_fields(self) -> dict:
        """Create form field widgets."""
        config = self.original_config
        
        return {
            'max_chunk_size': TextArea(
                text=str(config['max_chunk_size']),
                height=1,
                width=10
            ),
            'match_preview_length': TextArea(
                text=str(config['match_preview_length']),
                height=1,
                width=10
            ),
            'multi_match_count': TextArea(
                text=str(config['multi_match_count']),
                height=1,
                width=10
            ),
            'piping_threshold': TextArea(
                text=str(config['piping_threshold']),
                height=1,
                width=10
            ),
            'piping_max_context': TextArea(
                text=str(config['piping_max_context']),
                height=1,
                width=10
            ),
            'show_scores': CheckBox(
                text='show_scores',
                checked=config['show_scores']
            )
        }
    
    def _validate_field(self, name: str, value: str) -> tuple[bool, str]:
        """Validate field value. Returns (is_valid, error_message)."""
        ranges = {
            'max_chunk_size': (100, 50000),
            'match_preview_length': (50, 10000),
            'multi_match_count': (1, 10),
            'piping_threshold': (1000, 100000),
            'piping_max_context': (1000, 50000)
        }
        
        if name not in ranges:
            return True, ""
        
        try:
            int_val = int(value)
            min_val, max_val = ranges[name]
            if int_val < min_val or int_val > max_val:
                return False, f"Must be between {min_val}-{max_val}"
            return True, ""
        except ValueError:
            return False, "Must be a number"
    
    def _create_layout(self) -> Layout:
        """Build the TUI layout."""
        # Field rows
        field_rows = []
        
        # Output settings
        field_rows.append(Label('Output Settings:'))
        field_rows.append(
            VSplit([
                Label('  max_chunk_size:       '),
                self.fields['max_chunk_size'],
                Label(' chars (single match output)')
            ])
        )
        field_rows.append(
            VSplit([
                Label('  match_preview_length: '),
                self.fields['match_preview_length'],
                Label(' chars (preview per match)')
            ])
        )
        field_rows.append(
            VSplit([
                Label('  multi_match_count:    '),
                self.fields['multi_match_count'],
                Label(' matches (how many to show)')
            ])
        )
        
        field_rows.append(Label(''))  # Blank line
        
        # Piping settings
        field_rows.append(Label('Piping Settings:'))
        field_rows.append(
            VSplit([
                Label('  piping_threshold:     '),
                self.fields['piping_threshold'],
                Label(' chars (when /ask truncates)')
            ])
        )
        field_rows.append(
            VSplit([
                Label('  piping_max_context:   '),
                self.fields['piping_max_context'],
                Label(' chars (max context to /ask)')
            ])
        )
        
        field_rows.append(Label(''))  # Blank line
        
        # Display options
        field_rows.append(Label('Display Options:'))
        field_rows.append(
            VSplit([
                Label('  '),
                self.fields['show_scores'],
                Label(' Show relevance scores with matches')
            ])
        )
        
        field_rows.append(Label(''))  # Blank line
        field_rows.append(Label(''))  # Blank line
        
        # Buttons
        save_button = Button('SAVE', handler=self._on_save)
        cancel_button = Button('CANCEL', handler=self._on_cancel)
        
        button_row = VSplit([
            Window(width=30),  # Spacer
            save_button,
            Label('  '),
            cancel_button
        ])
        
        field_rows.append(button_row)
        field_rows.append(Label(''))  # Blank line
        field_rows.append(Label('Tab/Shift+Tab: Navigate  |  Enter: Edit field  |  Esc: Cancel'))
        
        # Wrap in frame
        content = Frame(
            HSplit(field_rows),
            title='Collections Configuration'
        )
        
        return Layout(content)
    
    def _on_save(self):
        """Save config and close."""
        # Validate all fields
        for name, widget in self.fields.items():
            if name == 'show_scores':
                continue  # Checkbox, always valid
            
            value = widget.text
            is_valid, error = self._validate_field(name, value)
            if not is_valid:
                # TODO: Show error, don't close
                return
        
        # Update config
        mine_config = {}
        for name, widget in self.fields.items():
            if name == 'show_scores':
                mine_config[name] = widget.checked
            else:
                mine_config[name] = int(widget.text)
        
        self.session.config['mine'] = mine_config
        
        # Save to disk
        config_file = Path.home() / '.isaac' / 'config.json'
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(self.session.config, f, indent=2)
        
        # Close app
        self.app.exit()
    
    def _on_cancel(self):
        """Close without saving."""
        self.app.exit()
    
    def _create_keybindings(self) -> KeyBindings:
        """Set up keyboard shortcuts."""
        kb = KeyBindings()
        
        @kb.add('escape')
        def _(event):
            """Escape = Cancel"""
            self._on_cancel()
        
        return kb
    
    def run(self):
        """Launch the TUI."""
        self.app = Application(
            layout=self._create_layout(),
            key_bindings=self._create_keybindings(),
            full_screen=True,
            mouse_support=True
        )
        
        self.app.run()


# Entry point for /config console command
def show_config_console(session_manager):
    """Show the config console TUI."""
    console = ConfigConsole(session_manager)
    console.run()
```

## Integration

**Add to command router:**

```python
# isaac/core/command_router.py

def _handle_meta_command(self, input_text: str) -> CommandResult:
    # ... existing meta commands ...
    
    if input_text == '/config console':
        from isaac.ui.config_console import show_config_console
        show_config_console(self.session)
        return CommandResult(
            success=True,
            output="Config updated",
            exit_code=0
        )
```

**Update /mine commands to read config:**

```python
# isaac/commands/mine/run.py - Already implemented in _handle_dig
# Just need to ensure _get_mine_config() is used
```

## Dependencies

**Already have:**
- `prompt_toolkit` (Isaac already uses this)
- `json` (stdlib)
- `pathlib` (stdlib)

**No new dependencies needed!**

## Testing Workflow

```powershell
# 1. Launch Isaac
C:\> isaac

# 2. Open config console
isaac> /config console

# 3. Tab to max_chunk_size field, change to 5000
#    Tab to SAVE, press Enter

# 4. Test with new settings
isaac> /mine dig coolant | /ask what is this?
[Should show more content now]

# 5. Adjust again if needed
isaac> /config console
[Change piping_max_context to 15000]
[Save]

# 6. Test again
isaac> /mine dig coolant | /ask what is this?
[Even more context sent to AI]
```

## Future Expansion (Later)

**Once this works, we can add:**
- Tab system (AI, Cloud, Collections, etc.)
- More settings per tab
- Color themes
- Better error display
- Field help tooltips

**But for now:** Just `/mine` settings, single screen, Tab navigation, quick edits.

## Time Estimate

**Implementation:** 3-4 hours
- Basic layout: 1 hour
- Field validation: 1 hour  
- Save/load logic: 1 hour
- Testing/polish: 1 hour

**Priority:** HIGH - Needed for testing piping behavior

---

**Ready to implement?** This is the MVP - just enough to let you iterate on Collections settings while testing.
