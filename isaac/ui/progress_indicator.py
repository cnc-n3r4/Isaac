"""
Progress Indicator System
Visual progress tracking for agentic tasks and tool execution
"""

import time
import threading
from typing import Dict, Any, List, Optional
from enum import Enum


class ProgressStyle(Enum):
    """Progress bar styles"""
    BAR = "bar"           # [████████████░░░░] 60%
    DOTS = "dots"         # ●●●●●●○○○○○○○○ 6/14
    SPINNER = "spinner"   # ⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏
    PERCENT = "percent"   # 60.0%
    TEXT = "text"         # Processing...


class ProgressIndicator:
    """
    Visual progress tracking for agentic execution.

    Provides multiple progress display styles and integrates with streaming display.
    """

    SPINNER_CHARS = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def __init__(self, style: ProgressStyle = ProgressStyle.BAR, width: int = 20):
        self.style = style
        self.width = width
        self.current_progress = 0.0
        self.message = ""
        self.is_active = False
        self.start_time = 0.0
        self.spinner_index = 0

        # Threading for animation
        self.animation_thread: Optional[threading.Thread] = None
        self.stop_animation = threading.Event()

    def start(self, message: str = "Processing..."):
        """Start the progress indicator"""
        self.message = message
        self.current_progress = 0.0
        self.is_active = True
        self.start_time = time.time()
        self.stop_animation.clear()

        if self.style == ProgressStyle.SPINNER:
            self.animation_thread = threading.Thread(target=self._animate_spinner, daemon=True)
            self.animation_thread.start()

    def update(self, progress: float, message: Optional[str] = None):
        """Update progress (0.0 to 1.0)"""
        self.current_progress = max(0.0, min(1.0, progress))
        if message is not None:
            self.message = message

    def set_message(self, message: str):
        """Update the progress message"""
        self.message = message

    def complete(self, message: str = "Complete"):
        """Mark progress as complete"""
        self.current_progress = 1.0
        self.message = message
        self.is_active = False
        self.stop_animation.set()

        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)

    def fail(self, message: str = "Failed"):
        """Mark progress as failed"""
        self.message = message
        self.is_active = False
        self.stop_animation.set()

        if self.animation_thread and self.animation_thread.is_alive():
            self.animation_thread.join(timeout=1.0)

    def _animate_spinner(self):
        """Animate spinner in background thread"""
        while not self.stop_animation.is_set():
            self.spinner_index = (self.spinner_index + 1) % len(self.SPINNER_CHARS)
            time.sleep(0.1)

    def get_display_text(self) -> str:
        """Get the current display text for the progress indicator"""
        if not self.is_active and self.current_progress < 1.0:
            return ""

        if self.style == ProgressStyle.BAR:
            return self._get_bar_display()
        elif self.style == ProgressStyle.DOTS:
            return self._get_dots_display()
        elif self.style == ProgressStyle.SPINNER:
            return self._get_spinner_display()
        elif self.style == ProgressStyle.PERCENT:
            return self._get_percent_display()
        elif self.style == ProgressStyle.TEXT:
            return self._get_text_display()
        else:
            return self.message

    def _get_bar_display(self) -> str:
        """Get progress bar display"""
        filled = int(self.width * self.current_progress)
        bar = "█" * filled + "░" * (self.width - filled)
        percent = f"{self.current_progress * 100:.1f}%"
        return f"[{bar}] {percent} {self.message}"

    def _get_dots_display(self) -> str:
        """Get dots progress display"""
        filled = int(self.width * self.current_progress)
        dots = "●" * filled + "○" * (self.width - filled)
        count = f"{filled}/{self.width}"
        return f"{dots} {count} {self.message}"

    def _get_spinner_display(self) -> str:
        """Get spinner display"""
        spinner = self.SPINNER_CHARS[self.spinner_index]
        return f"{spinner} {self.message}"

    def _get_percent_display(self) -> str:
        """Get percentage display"""
        percent = f"{self.current_progress * 100:.1f}%"
        return f"{percent} {self.message}"

    def _get_text_display(self) -> str:
        """Get text-only display"""
        return self.message

    def get_eta(self) -> Optional[float]:
        """Estimate time remaining"""
        if not self.is_active or self.current_progress <= 0:
            return None

        elapsed = time.time() - self.start_time
        if self.current_progress > 0:
            total_estimated = elapsed / self.current_progress
            remaining = total_estimated - elapsed
            return max(0, remaining)
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get progress statistics"""
        eta = self.get_eta()
        elapsed = time.time() - self.start_time if self.start_time > 0 else 0

        return {
            "progress": self.current_progress,
            "message": self.message,
            "is_active": self.is_active,
            "elapsed_seconds": elapsed,
            "eta_seconds": eta,
            "style": self.style.value
        }


class MultiProgressTracker:
    """
    Track multiple concurrent progress indicators.

    Useful for agentic execution with multiple parallel tools.
    """

    def __init__(self):
        self.indicators: Dict[str, ProgressIndicator] = {}
        self.lock = threading.Lock()

    def create_indicator(self, id: str, style: ProgressStyle = ProgressStyle.BAR) -> ProgressIndicator:
        """Create a new progress indicator"""
        with self.lock:
            indicator = ProgressIndicator(style)
            self.indicators[id] = indicator
            return indicator

    def get_indicator(self, id: str) -> Optional[ProgressIndicator]:
        """Get an existing progress indicator"""
        with self.lock:
            return self.indicators.get(id)

    def remove_indicator(self, id: str):
        """Remove a progress indicator"""
        with self.lock:
            if id in self.indicators:
                self.indicators[id].complete("Removed")
                del self.indicators[id]

    def get_all_display_text(self) -> List[str]:
        """Get display text for all active indicators"""
        with self.lock:
            return [
                f"{id}: {indicator.get_display_text()}"
                for id, indicator in self.indicators.items()
                if indicator.is_active or indicator.current_progress < 1.0
            ]

    def get_overall_progress(self) -> float:
        """Get overall progress across all indicators"""
        with self.lock:
            if not self.indicators:
                return 0.0

            active_indicators = [
                ind for ind in self.indicators.values()
                if ind.is_active or ind.current_progress < 1.0
            ]

            if not active_indicators:
                return 1.0

            return sum(ind.current_progress for ind in active_indicators) / len(active_indicators)

    def complete_all(self, message: str = "All tasks complete"):
        """Complete all indicators"""
        with self.lock:
            for indicator in self.indicators.values():
                indicator.complete(message)
            self.indicators.clear()

    def fail_all(self, message: str = "Tasks failed"):
        """Fail all indicators"""
        with self.lock:
            for indicator in self.indicators.values():
                indicator.fail(message)
            self.indicators.clear()