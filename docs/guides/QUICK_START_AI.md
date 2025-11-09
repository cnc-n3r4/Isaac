# Isaac AI System - Quick Start Guide

## 🚀 You're Ready to Go!

The AI routing system is fully built and operational. Here's how to start using it.

---

## Step 1: Set API Keys

Choose at least one provider:

```bash
# Option 1: Grok (Primary - Fast & Cheap)
export XAI_API_KEY='your-xai-api-key'

# Option 2: Claude (Fallback - Smart)
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# Option 3: OpenAI (Backup - Reliable)
export OPENAI_API_KEY='your-openai-api-key'
```

**Recommendation:** Set all three for maximum reliability!

---

## Step 2: Try It Out

### Option A: Run the Demo

```bash
cd /home/birdman/Projects/Isaac
source venv/bin/activate
python demo_agent.py
```

This demonstrates:
- File operations with AI
- Tool calling in action
- Usage statistics
- Multi-turn conversations

### Option B: Run the Tests

```bash
python test_ai_router.py
```

This tests:
- Basic chat
- Tool calling
- Provider fallback
- Statistics tracking

### Option C: Use It Directly

```python
from isaac.ai import IsaacAgent

# Create agent
agent = IsaacAgent()

# Chat with automatic tool execution
result = agent.chat("List all Python files in isaac/tools")

print(result['response'])
print(f"Tools used: {len(result['tool_executions'])}")
```

---

## What You Can Do

### 📖 Read Files
```python
agent.chat("Read the README.md file")
```

### 📝 Write Files
```python
agent.chat("Create a file called test.txt with 'Hello World'")
```

### ✏️ Edit Files
```python
agent.chat("Change 'debug = True' to 'debug = False' in config.py")
```

### 🔍 Search Code
```python
agent.chat("Find all TODO comments in Python files")
```

### 📂 Find Files
```python
agent.chat("List all JavaScript files in the src directory")
```

### 💬 General Questions
```python
agent.chat("Explain how the AIRouter works")
```

---

## Key Files

**Main Code:**
- `isaac/ai/agent.py` - AI agent (high-level interface)
- `isaac/ai/router.py` - Multi-provider router
- `isaac/ai/*_client.py` - Provider implementations

**Tools:**
- `isaac/tools/file_ops.py` - Read, Write, Edit
- `isaac/tools/code_search.py` - Grep, Glob

**Testing:**
- `test_ai_router.py` - Test suite
- `demo_agent.py` - Interactive demo

**Documentation:**
- `isaac/ai/README.md` - Complete AI documentation
- `isaac/tools/README.md` - Tools documentation
- `AI_ROUTING_BUILD_SUMMARY.md` - Build details

---

## Configuration

Default config is created at: `~/.isaac/ai_config.json`

**Customize it:**
```python
from isaac.ai import AIConfigManager

config = AIConfigManager()

# Change preferred provider
config.set_preferred_provider('claude')

# Set cost limit
config.set('routing.cost_limit_daily', 20.0)

# Change model
config.set('providers.grok.model', 'grok-2')
```

---

## Monitor Costs

```python
from isaac.ai import IsaacAgent

agent = IsaacAgent()

# Make some calls...
agent.chat("Hello")

# Check costs
stats = agent.get_stats()
print(f"Total cost today: ${stats['total_cost']:.4f}")
print(f"Remaining budget: ${stats['cost_remaining']:.2f}")
```

---

## Troubleshooting

### "No API keys found"
- Set at least one: `export XAI_API_KEY='...'`
- Check environment: `echo $XAI_API_KEY`

### "All providers failed"
- Check API key is valid
- Verify internet connection
- Check provider status pages

### "Import errors"
- Activate venv: `source venv/bin/activate`
- Check you're in Isaac directory

---

## Provider Info

| Provider | Speed | Cost  | Best For           |
|----------|-------|-------|--------------------|
| Grok     | Fast  | Low   | General queries    |
| Claude   | Med   | Med   | Complex reasoning  |
| OpenAI   | Fast  | Var   | Reliable fallback  |

**Fallback Order:** Grok → Claude → OpenAI

---

## Examples

### Simple Chat
```python
from isaac.ai import AIRouter

router = AIRouter()
response = router.chat(
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.content)
```

### With Tools
```python
from isaac.ai import IsaacAgent

agent = IsaacAgent()
result = agent.chat("Analyze the main.py file")
print(result['response'])
```

### Custom Configuration
```python
from isaac.ai import IsaacAgent, AIRouter

# Use specific provider
router = AIRouter()
response = router.chat(
    messages=[{"role": "user", "content": "Complex task"}],
    prefer_provider='claude'
)
```

---

## Next Steps

1. ✅ **Set API keys** (see Step 1)
2. ✅ **Run demo** (`python demo_agent.py`)
3. ✅ **Try some queries** (see examples above)
4. ✅ **Check costs** (monitor usage)
5. ✅ **Customize config** (adjust to your needs)
6. ✅ **Build something cool!**

---

## Get Help

- **Documentation:** See `isaac/ai/README.md`
- **API Reference:** Check inline docstrings
- **Examples:** Run `demo_agent.py` and `test_ai_router.py`
- **Issues:** Review build summary in `AI_ROUTING_BUILD_SUMMARY.md`

---

**You're all set! Start building with Isaac AI! 🚀**
