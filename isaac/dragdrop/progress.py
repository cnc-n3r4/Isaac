"""
Progress Indicators for Smart Drag-Drop System
Provides visual feedback during file processing operations.
"""

import sys
import time
import threading
from typing import Optional, Callable, Any
from enum import Enum


class ProgressStyle(Enum):
    """Different progress display styles"""
    PERCENTAGE = "percentage"  # 0-100% with bar
    SPINNER = "spinner"        # Spinning indicator
    DOTS = "dots"             # Progress dots
    SIMPLE = "simple"         # Simple text updates


class ProgressIndicator:
    """
    Visual progress indicator for long-running operations.
    """

    SPINNER_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, style: ProgressStyle = ProgressStyle.SPINNER,
                 prefix: str = "", suffix: str = ""):
        self.style = style
        self.prefix = prefix
        self.suffix = suffix
        self._current = 0
        self._total = 100
        self._message = ""
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, message: str = "", total: int = 100) -> None:
        """Start the progress indicator."""
        self._current = 0
        self._total = total
        self._message = message
        self._running = True

        if self.style in [ProgressStyle.SPINNER, ProgressStyle.DOTS]:
            self._thread = threading.Thread(target=self._animate, daemon=True)
            self._thread.start()
        else:
            self._update_display()

    def update(self, current: Optional[int] = None, message: Optional[str] = None) -> None:
        """Update progress."""
        if current is not None:
            self._current = current
        if message is not None:
            self._message = message

        if not self._running:
            return

        if self.style in [ProgressStyle.SPINNER, ProgressStyle.DOTS]:
            # Animation thread will handle display
            pass
        else:
            self._update_display()

    def set_message(self, message: str) -> None:
        """Set the current message."""
        self._message = message
        if self.style not in [ProgressStyle.SPINNER, ProgressStyle.DOTS]:
            self._update_display()

    def increment(self, amount: int = 1) -> None:
        """Increment progress by amount."""
        self._current += amount
        self.update()

    def complete(self, message: str = "Complete") -> None:
        """Mark progress as complete."""
        self._current = self._total
        self._message = message
        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)

        self._update_display(final=True)
        print()  # New line after completion

    def fail(self, message: str = "Failed") -> None:
        """Mark progress as failed."""
        self._message = message
        self._running = False

        if self._thread:
            self._thread.join(timeout=1.0)

        self._update_display(final=True)
        print()  # New line after failure

    def _animate(self) -> None:
        """Animation loop for spinner/dots styles."""
        frame = 0
        while self._running:
            self._update_display(frame=frame)
            frame = (frame + 1) % len(self.SPINNER_CHARS)
            time.sleep(0.1)

    def _update_display(self, frame: int = 0, final: bool = False) -> None:
        """Update the display."""
        # Clear current line
        print('\r' + ' ' * 80 + '\r', end='', flush=True)

        display = self.prefix

        if self.style == ProgressStyle.PERCENTAGE:
            percentage = int((self._current / self._total) * 100) if self._total > 0 else 0
            bar_width = 20
            filled = int(bar_width * self._current / self._total) if self._total > 0 else 0
            bar = '█' * filled + '░' * (bar_width - filled)
            display += f"[{bar}] {percentage:3d}% {self._message}"

        elif self.style == ProgressStyle.SPINNER:
            spinner = self.SPINNER_CHARS[frame]
            display += f"{spinner} {self._message}"

        elif self.style == ProgressStyle.DOTS:
            dots = '.' * ((frame % 4) + 1)
            display += f"{self._message}{dots}"

        elif self.style == ProgressStyle.SIMPLE:
            display += f"{self._message}"

        display += self.suffix

        if final:
            display += " ✓" if "Complete" in self._message else " ❌"

        print(display, end='', flush=True)


class BatchProgressManager:
    """
    Manages progress for batch operations with multiple files.
    """

    def __init__(self, style: ProgressStyle = ProgressStyle.PERCENTAGE):
        self.style = style
        self._indicators: dict[str, ProgressIndicator] = {}
        self._current_operation = ""

    def start_batch(self, operation: str, total_files: int) -> Callable[[str], None]:
        """
        Start a batch operation and return a progress callback.

        Args:
            operation: Description of the operation
            total_files: Total number of files to process

        Returns:
            Progress callback function
        """
        self._current_operation = operation

        if self.style == ProgressStyle.PERCENTAGE:
            indicator = ProgressIndicator(
                style=ProgressStyle.PERCENTAGE,
                prefix=f"{operation}: "
            )
            indicator.start(f"Processing {total_files} files", total_files)
        else:
            indicator = ProgressIndicator(
                style=self.style,
                prefix=f"{operation}: "
            )
            indicator.start(f"Processing {total_files} files")

        operation_key = f"{operation}_{id(self)}"
        self._indicators[operation_key] = indicator

        def progress_callback(message: str) -> None:
            if "✅" in message or "❌" in message:
                # File completed/failed
                indicator.increment()
                indicator.set_message(message)
            else:
                # Progress message
                indicator.set_message(message)

        return progress_callback

    def complete_batch(self, success: bool = True, message: str = "") -> None:
        """Complete the current batch operation."""
        for indicator in self._indicators.values():
            if success:
                indicator.complete(message or "Batch complete")
            else:
                indicator.fail(message or "Batch failed")

        self._indicators.clear()

    def get_progress_callback(self, operation: str) -> Callable[[str], None]:
        """
        Get a progress callback for an operation.

        Args:
            operation: Operation name

        Returns:
            Progress callback function
        """
        def callback(message: str) -> None:
            print(f"[{operation}] {message}")

        return callback


class ProgressCallback:
    """
    Utility class for creating progress callbacks.
    """

    @staticmethod
    def console_callback(operation: str) -> Callable[[str], None]:
        """Create a simple console progress callback."""
        def callback(message: str) -> None:
            print(f"[{operation}] {message}")
        return callback

    @staticmethod
    def silent_callback() -> Callable[[str], None]:
        """Create a silent (no-op) progress callback."""
        return lambda message: None

    @staticmethod
    def aggregating_callback() -> tuple[Callable[[str], None], Callable[[], list[str]]]:
        """Create a callback that aggregates all messages."""
        messages = []

        def callback(message: str) -> None:
            messages.append(message)

        def get_messages() -> list[str]:
            return messages.copy()

        return callback, get_messages


# Convenience functions
def create_progress_indicator(style: ProgressStyle = ProgressStyle.SPINNER,
                            prefix: str = "", suffix: str = "") -> ProgressIndicator:
    """Create a progress indicator."""
    return ProgressIndicator(style, prefix, suffix)


def with_progress(operation: str, style: ProgressStyle = ProgressStyle.SPINNER):
    """
    Decorator to add progress indication to a function.

    Usage:
        @with_progress("Processing files", ProgressStyle.PERCENTAGE)
        def process_files(files):
            # Function implementation
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            indicator = ProgressIndicator(style, prefix=f"{operation}: ")
            indicator.start("Starting...")

            try:
                result = func(*args, **kwargs)
                indicator.complete("Done")
                return result
            except Exception as e:
                indicator.fail(f"Error: {e}")
                raise

        return wrapper
    return decorator