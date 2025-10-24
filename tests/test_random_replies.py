"""Tests for random reply generator."""

import pytest
from pathlib import Path
from isaac.core.random_replies import RandomReplyGenerator, get_reply_generator


class TestRandomReplyGenerator:
    """Test the RandomReplyGenerator class."""

    def test_default_replies(self):
        """Test that default replies are loaded when no file is provided."""
        gen = RandomReplyGenerator()
        assert len(gen.replies) > 0
        
        # Should have at least the default replies
        reply = gen.get_reply()
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_custom_replies_file(self):
        """Test loading replies from a custom file."""
        # Create a temp file with custom replies
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Reply 1\n")
            f.write("Reply 2\n")
            f.write("Reply 3\n")
            f.write("# Comment line should be ignored\n")
            f.write("\n")  # Empty line should be ignored
            f.write("Reply 4\n")
            temp_path = f.name
        
        try:
            gen = RandomReplyGenerator(temp_path)
            assert len(gen.replies) == 4
            assert "Reply 1" in gen.replies
            assert "Reply 4" in gen.replies
            assert "# Comment line should be ignored" not in gen.replies
            
            # Test that get_reply returns one of our custom replies
            reply = gen.get_reply()
            assert reply in ["Reply 1", "Reply 2", "Reply 3", "Reply 4"]
        finally:
            Path(temp_path).unlink()

    def test_missing_file_uses_defaults(self):
        """Test that missing file falls back to defaults."""
        gen = RandomReplyGenerator("/nonexistent/file.txt")
        assert len(gen.replies) > 0
        reply = gen.get_reply()
        assert isinstance(reply, str)

    def test_prefix_required_reply(self):
        """Test the prefix_required_reply method."""
        gen = RandomReplyGenerator()
        reply = gen.get_prefix_required_reply()
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_command_failed_reply(self):
        """Test the command_failed_reply method."""
        gen = RandomReplyGenerator()
        reply = gen.get_command_failed_reply()
        assert isinstance(reply, str)
        assert len(reply) > 0

    def test_reload(self):
        """Test reloading replies."""
        gen = RandomReplyGenerator()
        original_count = len(gen.replies)
        
        # Reload with same settings
        gen.reload()
        assert len(gen.replies) == original_count

    def test_empty_file_uses_defaults(self):
        """Test that empty file falls back to defaults."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("")  # Empty file
            temp_path = f.name
        
        try:
            gen = RandomReplyGenerator(temp_path)
            assert len(gen.replies) > 0  # Should have defaults
        finally:
            Path(temp_path).unlink()


class TestGlobalGenerator:
    """Test the global reply generator functions."""

    def test_get_reply_generator(self):
        """Test the global get_reply_generator function."""
        # Reset global state
        import isaac.core.random_replies as module
        module._reply_generator = None
        
        gen1 = get_reply_generator()
        gen2 = get_reply_generator()
        
        # Should return same instance
        assert gen1 is gen2

    def test_get_reply_generator_with_config(self):
        """Test get_reply_generator with config dict."""
        # Reset global state
        import isaac.core.random_replies as module
        module._reply_generator = None
        
        config = {
            'random_replies_file': 'isaac/data/random_replies.txt'
        }
        
        gen = get_reply_generator(config)
        assert gen is not None
        assert len(gen.replies) > 0
