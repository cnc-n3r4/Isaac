"""Random reply generator for Isaac's personality responses."""

import random
from pathlib import Path
from typing import List, Optional


class RandomReplyGenerator:
    """Generates random sassy/funny replies for failed commands."""
    
    def __init__(self, replies_file: Optional[str] = None):
        """
        Initialize the random reply generator.
        
        Args:
            replies_file: Path to a text file with replies (one per line).
                         If None, uses default embedded replies.
        """
        self.replies: List[str] = []
        self._load_replies(replies_file)
    
    def _load_replies(self, replies_file: Optional[str] = None):
        """Load replies from file or use defaults."""
        if replies_file:
            try:
                file_path = Path(replies_file).expanduser()
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.replies = [
                            line.strip() 
                            for line in f 
                            if line.strip() and not line.strip().startswith('#')
                        ]
                    if self.replies:
                        return
            except Exception:
                pass  # Fall back to defaults
        
        # Default replies if file not found or empty
        self.replies = [
            "I have a name, use it.",
            "HaHa! What are you trying to do?",
            "OOPS! Do you realize what you've done!",
            "Not gonna work, pally",
            "No way, José. Josə? Jōse? meh, I can't spell either.",
            "What are ya, stupid?",
            "GTFOH! That doesn't work. Never has!",
            "Fat-fingers or blind?",
            "Keep tryin', you might get it.",
            "Swing and a miss, slugger!",
            "That's... creative. Wrong, but creative.",
            "Command not found. Shocking.",
            "Did autocorrect betray you?",
            "If ya don't make dollars, ya don't make ¢",
            "Nope. Try English next time.",
            "Close enough? Ha, no.",
            "Error: Brain not connected.",
            "Keep swinging, Rocky.",
            "That's a plot twist I didn't need.",
            "Fat thumbs strike again?",
            "Not even in the ballpark, Jack.",
            "Retry: Take 2 (or 20).",
            "What fresh hell is this?",
            "Invalid. Like your parking.",
            "You're inventing commands now? Bold.",
            "Backspace is your friend.",
            "That's adorable. Still busted.",
            "Nope-ify that noise.",
            "Command fail: Level expert.",
            "Oof. The humanity.",
            "The sad horn blow.. Womp, Woooomp"
        ]
    
    def get_reply(self) -> str:
        """Get a random reply from the loaded replies."""
        if not self.replies:
            return "I have a name, use it."  # Ultimate fallback
        return random.choice(self.replies)
    
    def get_prefix_required_reply(self) -> str:
        """Get a reply specifically for when 'isaac' prefix is missing."""
        return self.get_reply()
    
    def get_command_failed_reply(self) -> str:
        """Get a reply for when a command fails."""
        return self.get_reply()
    
    def reload(self, replies_file: Optional[str] = None):
        """Reload replies from file."""
        self.replies = []
        self._load_replies(replies_file)


# Global instance with configurable path
_reply_generator: Optional[RandomReplyGenerator] = None


def get_reply_generator(config: Optional[dict] = None) -> RandomReplyGenerator:
    """
    Get or create the global reply generator instance.
    
    Args:
        config: Optional config dict to get 'random_replies_file' from.
                If provided on first call, it will be used to initialize the generator.
    
    Returns:
        RandomReplyGenerator instance
    """
    global _reply_generator
    if _reply_generator is None:
        replies_file = None
        if config:
            replies_file = config.get('random_replies_file')
        _reply_generator = RandomReplyGenerator(replies_file)
    return _reply_generator


def get_random_reply() -> str:
    """Convenience function to get a random reply."""
    return get_reply_generator().get_reply()
