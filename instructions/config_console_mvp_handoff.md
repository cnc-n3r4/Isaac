# Config Console MVP - Implementation Handoff

**Status:** Ready for Implementation  
**Priority:** HIGH - Needed for Collections testing workflow  
**Estimated Time:** 3-4 hours  
**Complexity:** Medium  

## What to Build

A minimal TUI config console for `/mine` Collections settings. User can pop it up with `/config console`, tweak settings with Tab navigation, Save, and immediately test with new values.

## Spec Location

**Complete spec:** `.claude/mail/to_implement/mvp_config_console_spec.md`

Read that file for full details. Key points below:

## Key Requirements

### 1. The Cool Part - ISAAC 2.0 ASCII Art Header

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  ┳┏┓┏┓┏┓┏┓  ┏┓ ┏┓                                                            │
├─ ┃┗┓┣┫┣┫┃   ┏┛ ┃┃ ─────────────── COLLECTIONS ───────────── CONTROL CONSOLE ─┤
│  ┻┗┛┛┗┛┗┗┛  ┗━•┗┛                                                            │
```

**This is the signature element** - must look exactly like this with Unicode box-drawing characters.

### 2. Settings to Expose (6 total)

**Numeric fields:**
- `max_chunk_size` (100-50000, default 2000)
- `match_preview_length` (50-10000, default 500)
- `multi_match_count` (1-10, default 3)
- `piping_threshold` (1000-100000, default 10000)
- `piping_max_context` (1000-50000, default 8000)

**Checkbox:**
- `show_scores` (boolean, default true)

### 3. Simple Controls

- **Tab/Shift+Tab** - Navigate fields
- **Enter** - Edit focused field
- **Type** - Update numbers
- **Space** - Toggle checkbox
- **Esc** - Cancel and close
- **Tab to SAVE + Enter** - Save and close

### 4. Data Flow

**Load:** Read from `~/.isaac/config.json` → `config['mine']` section  
**Save:** Write back to `config['mine']`, persist to disk  
**Defaults:** If `mine` section missing, use defaults from spec  

### 5. Integration Point

```python
# isaac/core/command_router.py

if input_text == '/config console':
    from isaac.ui.config_console import show_config_console
    show_config_console(self.session)
    return CommandResult(success=True, output="", exit_code=0)
```

### 6. Tech Stack

- **Framework:** `prompt_toolkit` (already a dependency)
- **Widgets:** TextArea, CheckBox, Button, Label, Frame
- **Layout:** HSplit, VSplit, Window
- **No new dependencies needed**

## File to Create

**`isaac/ui/config_console.py`**

Main class: `ConfigConsole`  
Entry point: `show_config_console(session_manager)`

## Testing Workflow

```powershell
# User testing Collections, output too truncated
isaac> /mine dig coolant | /ask what is this?

# Pop up config console
isaac> /config console

# Tab to max_chunk_size, change 2000 → 5000
# Tab to SAVE, press Enter

# Test again with new settings
isaac> /mine dig coolant | /ask what is this?
[Should show more content now]
```

## Acceptance Criteria

- [ ] `/config console` opens TUI with ISAAC ASCII art header
- [ ] All 6 settings displayed with current values
- [ ] Tab navigation works between fields
- [ ] Numeric validation enforces min/max ranges
- [ ] Invalid input shows error (red border or message)
- [ ] Save button writes to `~/.isaac/config.json`
- [ ] Settings persist across Isaac restarts
- [ ] Cancel/Esc closes without saving
- [ ] TUI closes cleanly, returns to normal shell prompt
- [ ] `/mine dig` and `/ask` piping use new config values immediately

## Implementation Notes

**Read the full spec** for:
- Complete code structure with `ConfigConsole` class
- Border character constants
- Layout building logic
- Validation functions
- Field creation examples

**Don't overthink it:**
- Single screen only (no tabs yet - that's Phase 2)
- No animation, no colors (unless easy)
- Focus on function: quick edits, Tab navigation, Save/Cancel

**The header is critical:**
- Must use exact Unicode box-drawing characters
- ISAAC ASCII art must render correctly
- This is what makes it "cool" - don't skip it

## Phase 2 (Future - Not Now)

Later we'll add:
- Tabs for AI, Cloud, General settings
- More settings per tab
- Color themes
- Better validation feedback

**But for now:** Just the Collections settings, single screen, ISAAC header, Tab/Save/Cancel.

## Questions?

- Spec unclear? → Check `.claude/mail/to_implement/mvp_config_console_spec.md`
- prompt_toolkit examples? → They're in the spec
- Config file format? → Look at existing `~/.isaac/config.json`
- Integration point? → See `isaac/core/command_router.py` for other meta-commands

---

**Ready to build!** This is the foundation for Isaac's config UI system. Keep it simple, make it work, nail that ISAAC header. 🎯
