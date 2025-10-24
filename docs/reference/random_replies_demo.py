#!/usr/bin/env python3
"""
Demo: Random Reply Generator in Action

This script demonstrates how Isaac's random reply generator provides
varied, entertaining responses for failed commands and missing prefixes.
"""

from isaac.core.random_replies import get_reply_generator
import isaac.core.random_replies as module


def demo_default_replies():
    """Show default replies (no custom file)."""
    print("=" * 60)
    print("DEMO 1: Default Replies (Built-in)")
    print("=" * 60)
    
    # Reset to use defaults
    module._reply_generator = None
    gen = get_reply_generator()
    
    print(f"Loaded {len(gen.replies)} default replies\n")
    print("Simulating 5 failed attempts:\n")
    
    for i in range(5):
        print(f"isaac> what is the weather")
        print(f"Isaac > {gen.get_prefix_required_reply()}\n")


def demo_custom_replies():
    """Show custom replies from file."""
    print("\n" + "=" * 60)
    print("DEMO 2: Custom Replies (From File)")
    print("=" * 60)
    
    # Reset and load custom file
    module._reply_generator = None
    config = {'random_replies_file': 'isaac/data/random_replies.txt'}
    gen = get_reply_generator(config)
    
    print(f"Loaded {len(gen.replies)} custom replies\n")
    print("Simulating 5 failed attempts:\n")
    
    for i in range(5):
        print(f"isaac> tell me a joke")
        print(f"Isaac > {gen.get_prefix_required_reply()}\n")


def demo_variety():
    """Show the variety of responses."""
    print("\n" + "=" * 60)
    print("DEMO 3: Reply Variety")
    print("=" * 60)
    
    module._reply_generator = None
    config = {'random_replies_file': 'isaac/data/random_replies.txt'}
    gen = get_reply_generator(config)
    
    # Collect 20 samples
    replies = [gen.get_reply() for _ in range(20)]
    unique_replies = set(replies)
    
    print(f"Generated 20 replies")
    print(f"Unique replies: {len(unique_replies)}")
    print(f"Uniqueness rate: {len(unique_replies)/20*100:.1f}%\n")
    
    print("All unique replies seen:")
    for i, reply in enumerate(sorted(unique_replies), 1):
        print(f"  {i}. {reply}")


def demo_comparison():
    """Compare before/after with static message."""
    print("\n" + "=" * 60)
    print("DEMO 4: Before vs After")
    print("=" * 60)
    
    print("\n--- BEFORE (Static Message) ---")
    print("isaac> hello there")
    print("Isaac > I have a name, use it.")
    print("\nisaac> what's the time")
    print("Isaac > I have a name, use it.")
    print("\nisaac> tell me something")
    print("Isaac > I have a name, use it.")
    print("\n(Gets boring and repetitive...)")
    
    print("\n--- AFTER (Random Replies) ---")
    module._reply_generator = None
    config = {'random_replies_file': 'isaac/data/random_replies.txt'}
    gen = get_reply_generator(config)
    
    commands = ["hello there", "what's the time", "tell me something"]
    for cmd in commands:
        print(f"\nisaac> {cmd}")
        print(f"Isaac > {gen.get_reply()}")
    print("\n(Much more engaging and fun!)")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ISAAC RANDOM REPLY GENERATOR DEMO" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    
    demo_default_replies()
    demo_custom_replies()
    demo_variety()
    demo_comparison()
    
    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nTo configure your own custom replies:")
    print("  1. Create a text file with replies (one per line)")
    print("  2. Add to ~/.isaac/config.json:")
    print('     {"random_replies_file": "path/to/your/replies.txt"}')
    print("  3. Restart Isaac")
    print("\n")
