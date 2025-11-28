"""
Advanced Input Handler for Isaac UI

Provides advanced keyboard input handling with custom key bindings,
input validation, and rich terminal interactions.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from prompt_toolkit.key_binding import KeyBindings, KeyPressEvent
from prompt_toolkit.keys import Keys


class AdvancedInputHandler:
    """
    Advanced input handler with custom key bindings and validation.
    
    Features:
    - Custom key bindings (Ctrl+C, Ctrl+D, Tab, etc.)
    - Input validation and sanitization
    - Multi-line input support
    - Auto-completion integration
    - Command history navigation
    """
    
    def __init__(self):
        """Initialize the advanced input handler."""
        self.key_bindings = self._create_default_bindings()
        self.validators: List[Callable[[str], bool]] = []
        self.transformers: List[Callable[[str], str]] = []
    
    def _create_default_bindings(self) -> KeyBindings:
        """Create default key bindings."""
        kb = KeyBindings()
        
        @kb.add(Keys.ControlC)
        def _(event: KeyPressEvent):
            """Handle Ctrl+C - Cancel current input."""
            event.app.exit(exception=KeyboardInterrupt)
        
        @kb.add(Keys.ControlD)
        def _(event: KeyPressEvent):
            """Handle Ctrl+D - Exit on empty input."""
            buffer = event.app.current_buffer
            if not buffer.text:
                event.app.exit()
        
        @kb.add(Keys.Tab)
        def _(event: KeyPressEvent):
            """Handle Tab - Auto-completion."""
            event.current_buffer.complete_next()
        
        return kb
    
    def add_key_binding(self, key: str, handler: Callable[[KeyPressEvent], None]):
        """
        Add a custom key binding.
        
        Args:
            key: Key combination (e.g., 'c-t' for Ctrl+T)
            handler: Function to handle the key press
        """
        @self.key_bindings.add(key)
        def _(event: KeyPressEvent):
            handler(event)
    
    def add_validator(self, validator: Callable[[str], bool]):
        """
        Add an input validator.
        
        Args:
            validator: Function that returns True if input is valid
        """
        self.validators.append(validator)
    
    def add_transformer(self, transformer: Callable[[str], str]):
        """
        Add an input transformer.
        
        Args:
            transformer: Function that transforms input text
        """
        self.transformers.append(transformer)
    
    def validate_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate input text against all validators.
        
        Args:
            text: Input text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        for validator in self.validators:
            try:
                if not validator(text):
                    return (False, "Input validation failed")
            except Exception as e:
                return (False, f"Validation error: {str(e)}")
        
        return (True, None)
    
    def transform_input(self, text: str) -> str:
        """
        Transform input text through all transformers.
        
        Args:
            text: Input text to transform
            
        Returns:
            Transformed text
        """
        result = text
        for transformer in self.transformers:
            try:
                result = transformer(result)
            except Exception:
                pass  # Skip failed transformations
        
        return result
    
    def get_key_bindings(self) -> KeyBindings:
        """Get the key bindings object."""
        return self.key_bindings


class MultiLineInputHandler(AdvancedInputHandler):
    """
    Input handler with multi-line support.
    
    Features:
    - Meta+Enter or Ctrl+Enter for multi-line
    - Proper indentation handling
    - Code block detection
    """
    
    def __init__(self):
        """Initialize multi-line input handler."""
        super().__init__()
        self._setup_multiline_bindings()
    
    def _setup_multiline_bindings(self):
        """Setup multi-line specific key bindings."""
        @self.key_bindings.add('escape', 'enter')  # Meta+Enter
        def _(event: KeyPressEvent):
            """Insert newline on Meta+Enter."""
            event.current_buffer.insert_text('\n')
        
        @self.key_bindings.add('c-enter')  # Ctrl+Enter
        def _(event: KeyPressEvent):
            """Insert newline on Ctrl+Enter."""
            event.current_buffer.insert_text('\n')


# Convenience function for creating handlers
def create_input_handler(multi_line: bool = False) -> AdvancedInputHandler:
    """
    Create an input handler.
    
    Args:
        multi_line: Whether to support multi-line input
        
    Returns:
        AdvancedInputHandler instance
    """
    if multi_line:
        return MultiLineInputHandler()
    return AdvancedInputHandler()


__all__ = [
    'AdvancedInputHandler',
    'MultiLineInputHandler',
    'create_input_handler',
]
