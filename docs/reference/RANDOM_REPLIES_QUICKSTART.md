# Random Replies - Quick Start Guide

Get Isaac to respond with random sassy/funny messages instead of the same error over and over!

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Your Replies File

Create a text file with your favorite replies, one per line:

```bash
# On Windows
notepad %USERPROFILE%\.isaac\custom_replies.txt

# On Linux/Mac
nano ~/.isaac/custom_replies.txt
```

Add some replies:
```text
Swing and a miss, slugger!
What fresh hell is this?
Keep tryin', you might get it.
Command not found. Shocking.
Fat thumbs strike again?
Nope. Try English next time.
That's adorable. Still busted.
```

### Step 2: Configure Isaac

Edit your Isaac config:

```bash
# On Windows
notepad %USERPROFILE%\.isaac\config.json

# On Linux/Mac
nano ~/.isaac/config.json
```

Add this line (or update existing config.json):
```json
{
  "random_replies_file": "~/.isaac/custom_replies.txt"
}
```

### Step 3: Test It!

Restart Isaac and try a command without the 'isaac' prefix:

```bash
isaac> what is the weather
Isaac > Swing and a miss, slugger!

isaac> tell me a joke  
Isaac > What fresh hell is this?
```

Each time you get a **different random reply**! 🎉

## 📝 File Format Tips

### Good Replies
✅ One reply per line  
✅ Short and punchy  
✅ Sassy but friendly  
✅ Mix of humor styles  

### Example File
```text
# Friendly sass
Keep swinging, Rocky.
Swing and a miss, slugger!
Close enough? Ha, no.

# Technical humor
Command not found. Shocking.
Error: Brain not connected.
Syntax error: Line 1, User 0.

# Pop culture
What fresh hell is this?
Not even in the ballpark, Jack.
The sad horn blow.. Womp, Woooomp

# Empty lines and comments are ignored
```

### What Isaac Ignores
- Empty lines
- Lines starting with `#` (comments)
- Extra whitespace

## 🎯 Use Cases

### When You'll See Random Replies

1. **Forgetting 'isaac' prefix on natural language**
   ```bash
   isaac> what time is it
   Isaac > Did autocorrect betray you?
   ```
   Should be: `isaac what time is it`

2. **Failed command attempts** (can be extended to other errors)

## 🔧 Troubleshooting

### Not Working?

**Check file path:**
```bash
# Windows
dir %USERPROFILE%\.isaac\custom_replies.txt

# Linux/Mac
ls -la ~/.isaac/custom_replies.txt
```

**Check config:**
```bash
# Windows
type %USERPROFILE%\.isaac\config.json

# Linux/Mac  
cat ~/.isaac/config.json
```

**Test manually:**
```python
from isaac.core.random_replies import RandomReplyGenerator
gen = RandomReplyGenerator('~/.isaac/custom_replies.txt')
print(f"Loaded {len(gen.replies)} replies")
print(gen.get_reply())
```

### Still Using Defaults?

If Isaac can't find your file, it uses built-in defaults. This is **intentional** - Isaac always works!

Check:
- File path is correct (use absolute path to debug)
- File is readable (check permissions)
- Config JSON is valid (use jsonlint.com)

## 📚 More Info

- **Full docs:** `docs/reference/random_replies.md`
- **Demo script:** `python docs/reference/random_replies_demo.py`
- **Example config:** `docs/reference/config_example_random_replies.json`
- **Tests:** `pytest tests/test_random_replies.py -v`

## 🎨 Creative Ideas

### Themed Reply Sets

**Professional Mode:**
```text
Command requires clarification.
Syntax validation failed.
Input not recognized. Please retry.
```

**Maximum Sass Mode:**
```text
GTFOH! That doesn't work. Never has!
What are ya, stupid?
Fat-fingers or blind?
```

**Wholesome Mode:**
```text
Oops! Let's try that again.
Almost there! One more time.
Nice try! Here's what you need: isaac <your query>
```

### Context-Specific Replies

You could even create different files for different contexts and swap them:

```json
{
  "random_replies_file": "~/.isaac/replies_work.txt"
}
```

## 🌟 Pro Tips

1. **Keep it fresh** - Add new replies occasionally
2. **Test variety** - Run demo to see distribution
3. **Mix styles** - Blend humor, sass, and helpful hints
4. **Stay on brand** - Isaac is sassy but ultimately helpful
5. **Have fun** - This is YOUR assistant's personality!

---

**Ready to customize?** Edit your replies and make Isaac yours! 🚀
