#!/usr/bin/env python3
"""
Visual Enhancements Demo - Show off Isaac's new visual capabilities
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.ui.visual_enhancer import VisualEnhancer, Color


def demo_visual_enhancements():
    """Demonstrate visual enhancement features."""
    enhancer = VisualEnhancer()

    print("🎨 Isaac Visual Enhancements Demo")
    print("=" * 50)

    # Color demonstration
    print("\n1. Color Capabilities:")
    print(f"   {enhancer.colorize_text('RED', Color.RED)}")
    print(f"   {enhancer.colorize_text('GREEN', Color.GREEN)}")
    print(f"   {enhancer.colorize_text('BLUE', Color.BLUE)}")
    print(f"   {enhancer.colorize_text('BOLD', Color.BOLD)}")
    print(f"   {enhancer.colorize_text('BRIGHT CYAN', Color.BRIGHT_CYAN)}")

    # Command output formatting
    print("\n2. Command Output Formatting:")
    sample_output = enhancer.format_command_output(
        "ls -la",
        "total 42\ndrwxr-xr-x  5 user  staff  160 Jan 15 10:30 .\ndrwxr-xr-x  18 user  staff  576 Jan 15 10:25 ..",
        True
    )
    print(sample_output)

    # Error output
    print("\n3. Error Output Formatting:")
    error_output = enhancer.format_command_output(
        "rm -rf /",
        "rm: /: Permission denied",
        False
    )
    print(error_output)

    # Prompt formatting
    print("\n4. Prompt Formatting:")
    prompt = enhancer.format_prompt("isaac", "ready for commands")
    print(f"   {prompt}")

    # Welcome message
    print("\n5. Welcome Message:")
    welcome = enhancer.format_welcome_message()
    print(welcome)

    # Syntax highlighting demo
    print("\n6. Syntax Highlighting:")
    commands = [
        "ls -la /home/user",
        "git status --porcelain",
        "python3 -m pytest tests/",
        "docker build -t myapp .",
        "ssh user@server 'uptime'"
    ]

    for cmd in commands:
        highlighted = enhancer.highlight_syntax(cmd)
        print(f"   {highlighted}")

    print("\n" + "=" * 50)
    print("✨ Visual enhancements complete!")


if __name__ == "__main__":
    demo_visual_enhancements()