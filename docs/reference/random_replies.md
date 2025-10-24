# Random Reply Generator

Isaac features a random reply generator that provides sassy, funny responses when commands fail or when natural language queries are attempted without the `isaac` prefix.

## Overview

Instead of showing the same error message every time, Isaac randomly selects from a collection of witty replies to keep things entertaining while still being helpful.

## Configuration

To use custom replies, add the following to your Isaac config file (`~/.isaac/config.json`):

```json
{
  "random_replies_file": "/path/to/your/replies.txt"
}
```

Or use a relative path from your Isaac installation:

```json
{
  "random_replies_file": "isaac/data/random_replies.txt"
}
```

## Reply File Format

The replies file is a simple text file with one reply per line:

```text
HaHa! What are you trying to do?
OOPS! Do you realize what you've done!
Not gonna work, pally
No way, José. Josə? Jōse? meh, I can't spell either.
What are ya, stupid?
```

### File Format Rules

- **One reply per line** - Each line becomes a possible response
- **Empty lines are ignored** - Use them to organize your replies
- **Comments start with #** - Lines beginning with `#` are ignored
- **UTF-8 encoding** - Supports emojis and special characters

### Example File

```text
# Friendly responses
Keep tryin', you might get it.
Swing and a miss, slugger!
That's... creative. Wrong, but creative.

# Sassy responses
Command not found. Shocking.
Did autocorrect betray you?
Nope. Try English next time.

# Funny responses
Error: Brain not connected.
Fat thumbs strike again?
What fresh hell is this?
```

## Default Replies

If no custom file is configured or the file can't be loaded, Isaac uses a built-in set of default replies including:

- "I have a name, use it."
- "HaHa! What are you trying to do?"
- "Swing and a miss, slugger!"
- "Command not found. Shocking."
- "Keep swinging, Rocky."
- ...and 25+ more!

## Usage Examples

### When Natural Language Lacks Prefix

```bash
isaac> tell me a joke
Isaac > Nope. Try English next time.

isaac> what is the weather
Isaac > Fat thumbs strike again?
```

The correct format requires the `isaac` prefix:

```bash
isaac> isaac tell me a joke
Isaac > [AI response with actual joke]
```

### When Commands Fail

Random replies can also be used for various command failures throughout Isaac, providing personality and making error messages less monotonous.

## Implementation

### Using in Custom Code

```python
from isaac.core.random_replies import get_reply_generator

# Get the global instance (uses config automatically)
reply_gen = get_reply_generator(config)

# Get a random reply
reply = reply_gen.get_reply()
print(f"Isaac > {reply}")

# Get specific type of reply
prefix_reply = reply_gen.get_prefix_required_reply()
failed_reply = reply_gen.get_command_failed_reply()
```

### Creating Custom Instance

```python
from isaac.core.random_replies import RandomReplyGenerator

# Load from custom file
gen = RandomReplyGenerator('/path/to/replies.txt')

# Get a reply
reply = gen.get_reply()
```

## Best Practices

### Writing Good Replies

1. **Keep it short** - One-liners work best in terminal output
2. **Stay on brand** - Isaac has attitude but is ultimately helpful
3. **Avoid offensive content** - Sassy is good, mean isn't
4. **Be creative** - Mix humor styles (puns, references, sass)
5. **Test readability** - Make sure replies make sense out of context

### Good Examples

✅ "Swing and a miss, slugger!"  
✅ "That's adorable. Still busted."  
✅ "Command fail: Level expert."  
✅ "Keep swinging, Rocky."  

### Avoid

❌ Overly long explanations  
❌ Technical jargon that confuses users  
❌ Genuinely mean or offensive content  
❌ Inside jokes only you understand  

## Troubleshooting

### Replies Not Loading

If your custom replies aren't loading:

1. **Check file path** - Use absolute path or verify relative path is correct
2. **Verify file exists** - Make sure the file is readable
3. **Check encoding** - File should be UTF-8
4. **Test with defaults** - Remove config setting temporarily to verify system works

### Testing Your Replies

```python
from isaac.core.random_replies import RandomReplyGenerator

# Load your file
gen = RandomReplyGenerator('your_replies.txt')

# Verify it loaded
print(f"Loaded {len(gen.replies)} replies")

# Test a few
for i in range(5):
    print(f"{i+1}. {gen.get_reply()}")
```

## File Locations

### Default Replies File

```
isaac/data/random_replies.txt
```

### User Config File

```
~/.isaac/config.json
```

### Custom Replies (Recommended)

```
~/.isaac/custom_replies.txt
```

Then configure in `config.json`:

```json
{
  "random_replies_file": "~/.isaac/custom_replies.txt"
}
```

## Related Features

- **Error Handling** - Random replies integrate with Isaac's error system
- **Personality System** - Part of Isaac's overall personality and tone
- **Natural Language Processing** - Works with AI query detection
- **Config System** - Uses Isaac's standard configuration approach
