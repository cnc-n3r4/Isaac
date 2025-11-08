# Isaac AI Routing System

Multi-provider AI integration with intelligent fallback and tool calling support.

## Overview

Isaac's AI system provides:
- **Multi-Provider Support**: Grok (xAI), Claude (Anthropic), OpenAI
- **Intelligent Fallback**: Automatic provider switching on failures
- **Tool Calling**: File operations integrated with AI
- **Cost Tracking**: Monitor and limit API costs
- **Configurable**: Customizable models, prompts, and routing

## Architecture

```
┌─────────────┐
│ IsaacAgent  │  - High-level interface
│             │  - Tool execution
│             │  - Conversation management
└──────┬──────┘
       │
┌──────▼──────┐
│  AIRouter   │  - Provider fallback
│             │  - Cost tracking
│             │  - Usage statistics
└──────┬──────┘
       │
   ┌───┴───┬───────┬────────┐
   │       │       │        │
┌──▼──┐ ┌─▼───┐ ┌─▼────┐  │
│Grok │ │Claude│ │OpenAI│ Tools
│     │ │      │ │      │  │
│Fast │ │Smart │ │Reliable  ├─ Read
│Cheap│ │      │ │      │  ├─ Write
└─────┘ └──────┘ └──────┘  ├─ Edit
                            ├─ Grep
                            └─ Glob
```

## Quick Start

### 1. Set API Keys

```bash
export XAI_API_KEY='your-grok-key'
export ANTHROPIC_API_KEY='your-claude-key'
export OPENAI_API_KEY='your-openai-key'
```

### 2. Basic Usage

```python
from isaac.ai import IsaacAgent

# Create agent
agent = IsaacAgent()

# Chat with automatic tool execution
result = agent.chat("Read the README.md file")

print(result['response'])
print(f"Used {len(result['tool_executions'])} tools")
```

### 3. Direct Router Usage

```python
from isaac.ai import AIRouter

router = AIRouter()

messages = [
    {"role": "user", "content": "Hello!"}
]

response = router.chat(messages=messages)
print(f"Provider: {response.provider}")
print(f"Response: {response.content}")
```

## Components

### IsaacAgent

High-level agent with tool integration.

```python
from isaac.ai import IsaacAgent

agent = IsaacAgent()

# Set custom system prompt
agent.set_system_prompt('code_assistant')

# Chat with tools
result = agent.chat(
    "Find all Python files in the src directory",
    max_iterations=5
)

# Get statistics
stats = agent.get_stats()
print(f"Total cost: ${stats['total_cost']:.4f}")
```

**Methods:**
- `chat(message, max_iterations=5)` - Chat with tool execution
- `set_system_prompt(prompt_type)` - Set system prompt
- `reset_conversation()` - Clear history
- `get_stats()` - Get usage statistics
- `execute_tool(name, args)` - Execute tool directly

### AIRouter

Multi-provider router with fallback.

```python
from isaac.ai import AIRouter

router = AIRouter()

# Basic chat
response = router.chat(
    messages=[{"role": "user", "content": "Hi"}]
)

# With tools
from isaac.tools import ReadTool

tools = [ReadTool().get_parameters_schema()]

response = router.chat(
    messages=[{"role": "user", "content": "Use read tool"}],
    tools=tools
)

# Get statistics
stats = router.get_stats()
```

**Methods:**
- `chat(messages, tools=None, **kwargs)` - Send chat request
- `get_stats()` - Get usage statistics
- `reset_stats()` - Reset daily stats
- `get_available_providers()` - List active providers
- `update_config(updates)` - Update configuration

### AI Clients

Direct client access for each provider.

```python
from isaac.ai import GrokClient, ClaudeClient, OpenAIClient

# Grok (primary)
grok = GrokClient(api_key='your-key')
response = grok.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model='grok-beta',
    temperature=0.7
)

# Claude (fallback)
claude = ClaudeClient(api_key='your-key')
response = claude.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model='claude-3-5-sonnet-20241022'
)

# OpenAI (backup)
openai = OpenAIClient(api_key='your-key')
response = openai.chat(
    messages=[{"role": "user", "content": "Hello"}],
    model='gpt-4o-mini'
)
```

## Configuration

### Config File Location

`~/.isaac/ai_config.json`

### Default Configuration

```json
{
  "providers": {
    "grok": {
      "enabled": true,
      "api_key_env": "XAI_API_KEY",
      "model": "grok-beta",
      "timeout": 60,
      "max_retries": 2
    },
    "claude": {
      "enabled": true,
      "api_key_env": "ANTHROPIC_API_KEY",
      "model": "claude-3-5-sonnet-20241022",
      "timeout": 60,
      "max_retries": 1
    },
    "openai": {
      "enabled": true,
      "api_key_env": "OPENAI_API_KEY",
      "model": "gpt-4o-mini",
      "timeout": 60,
      "max_retries": 1
    }
  },
  "routing": {
    "strategy": "fallback",
    "prefer_provider": "grok",
    "cost_limit_daily": 10.0,
    "enable_tracking": true
  },
  "defaults": {
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

### Managing Configuration

```python
from isaac.ai import AIConfigManager

config = AIConfigManager()

# Get setting
model = config.get('providers.grok.model')

# Update setting
config.set('providers.grok.model', 'grok-2')

# Enable/disable providers
config.enable_provider('claude')
config.disable_provider('openai')

# Set preferred provider
config.set_preferred_provider('grok')

# Custom prompts
config.set_custom_prompt('my_prompt', 'You are a helpful assistant.')
prompt = config.get_custom_prompt('my_prompt')
```

## Tool Integration

All file operation tools are automatically available to the AI:

### Available Tools

1. **read** - Read file contents
2. **write** - Create files
3. **edit** - Edit files (exact replacement)
4. **grep** - Search files
5. **glob** - Find files by pattern

### Example Tool Usage

```python
agent = IsaacAgent()

# AI will use tools automatically
result = agent.chat("What's in the config file?")
# → Uses read tool

result = agent.chat("Create a README.md file")
# → Uses write tool

result = agent.chat("Change 'debug = True' to 'debug = False' in app.py")
# → Uses edit tool

result = agent.chat("Find all TODO comments in Python files")
# → Uses grep tool

result = agent.chat("List all JavaScript files")
# → Uses glob tool
```

## Provider Fallback

The router automatically falls back to the next provider on failure:

**Fallback Order:**
1. **Grok** (Primary) - Fast, cheap
2. **Claude** (Fallback) - Smart, complex tasks
3. **OpenAI** (Backup) - Reliable

**Fallback Triggers:**
- API timeout
- HTTP errors (rate limits, auth failures)
- Network errors
- Invalid responses

**Example:**

```python
router = AIRouter()

# Grok fails → falls back to Claude
# Claude fails → falls back to OpenAI
response = router.chat(messages=[...])

print(f"Used provider: {response.provider}")
```

## Cost Tracking

Track API usage and costs across all providers.

```python
router = AIRouter()

# Make some calls
for i in range(10):
    router.chat(messages=[{"role": "user", "content": "Hi"}])

# Get statistics
stats = router.get_stats()

print(f"Total calls: {stats['total_calls']}")
print(f"Total tokens: {stats['total_tokens']}")
print(f"Total cost: ${stats['total_cost']:.4f}")
print(f"Cost limit: ${stats['cost_limit']:.2f}")
print(f"Remaining: ${stats['cost_remaining']:.2f}")

# Per-provider breakdown
for provider, pstats in stats['usage'].items():
    print(f"\n{provider}:")
    print(f"  Calls: {pstats['calls']}")
    print(f"  Cost: ${pstats['cost']:.4f}")
    print(f"  Failures: {pstats['failures']}")

# Reset daily stats
router.reset_stats()
```

## Pricing (as of 2024)

### Grok (xAI)
- Input: $5/1M tokens
- Output: $15/1M tokens
- Best for: Fast, cost-effective queries

### Claude (Anthropic)
- Sonnet: $3 input, $15 output per 1M tokens
- Haiku: $1 input, $5 output per 1M tokens
- Opus: $15 input, $75 output per 1M tokens
- Best for: Complex reasoning, code analysis

### OpenAI
- GPT-4o: $2.50 input, $10 output per 1M tokens
- GPT-4o-mini: $0.15 input, $0.60 output per 1M tokens
- GPT-4-turbo: $10 input, $30 output per 1M tokens
- Best for: Reliable fallback

## Examples

### Example 1: Code Analysis

```python
from isaac.ai import IsaacAgent

agent = IsaacAgent()

result = agent.chat("""
Analyze the main.py file and tell me:
1. What does it do?
2. Are there any bugs?
3. How can it be improved?
""")

print(result['response'])
print(f"\nTools used: {len(result['tool_executions'])}")
for exec in result['tool_executions']:
    print(f"  - {exec['tool']}: {exec['arguments']}")
```

### Example 2: Batch File Operations

```python
agent = IsaacAgent()

result = agent.chat("""
Find all Python files in the src/ directory,
then search them for 'TODO' comments,
and create a file called todos.txt with the results.
""")

print(result['response'])
```

### Example 3: Provider-Specific Request

```python
from isaac.ai import AIRouter

router = AIRouter()

# Force specific provider
response = router.chat(
    messages=[{"role": "user", "content": "Complex analysis task"}],
    prefer_provider='claude'  # Use Claude for complex reasoning
)
```

### Example 4: Tool-Free Chat

```python
from isaac.ai import AIRouter

router = AIRouter()

# No tools, just conversation
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing"}
]

response = router.chat(messages=messages)
print(response.content)
```

## Testing

Run the test suite:

```bash
# Set API keys first
export XAI_API_KEY='your-key'
export ANTHROPIC_API_KEY='your-key'
export OPENAI_API_KEY='your-key'

# Run tests
cd /home/birdman/Projects/Isaac
source venv/bin/activate
python test_ai_router.py
```

## Error Handling

```python
from isaac.ai import IsaacAgent

agent = IsaacAgent()

result = agent.chat("Do something")

if result['success']:
    print(result['response'])
else:
    print(f"Error: {result['error']}")
    print(f"Iterations: {result['iterations']}")
    
# AIResponse also has error field
from isaac.ai import AIRouter

router = AIRouter()
response = router.chat(messages=[...])

if response.success:
    print(response.content)
else:
    print(f"Error: {response.error}")
```

## Best Practices

1. **Set API Keys**: Configure at least one provider
2. **Monitor Costs**: Check stats regularly with `get_stats()`
3. **Set Limits**: Configure `cost_limit_daily` in config
4. **Use Fallback**: Don't override `prefer_provider` unless needed
5. **Reset Stats**: Call `reset_stats()` daily
6. **Custom Prompts**: Create task-specific system prompts
7. **Iteration Limits**: Set appropriate `max_iterations` for safety
8. **Error Handling**: Always check `result['success']`

## Troubleshooting

### "No API keys found"
- Set environment variables: `export XAI_API_KEY='...'`
- Check `.env` file
- Verify key names match config

### "All providers failed"
- Check API key validity
- Verify internet connection
- Check API quotas/limits
- Review error messages in stats

### "Daily cost limit exceeded"
- Reset stats: `router.reset_stats()`
- Increase limit: `config.set('routing.cost_limit_daily', 20.0)`
- Check per-provider costs in stats

### Tools not working
- Verify tool schemas are registered
- Check file paths in tool arguments
- Review tool execution results
- Increase `max_iterations` if needed

## Advanced Usage

### Custom Tools

```python
from isaac.ai import IsaacAgent
from isaac.tools.base import BaseTool

class MyTool(BaseTool):
    # Implement custom tool
    pass

agent = IsaacAgent()
agent.tools['mytool'] = MyTool()
agent.tool_schemas.append(MyTool().get_parameters_schema())
```

### Streaming Responses

Coming soon - streaming support for real-time responses.

### Async Support

Coming soon - async/await support for concurrent requests.

## API Reference

See inline documentation:
- `isaac/ai/base.py` - Base classes
- `isaac/ai/router.py` - Router implementation
- `isaac/ai/agent.py` - Agent implementation
- `isaac/ai/config_manager.py` - Configuration

## Contributing

When adding new AI providers:
1. Create client in `isaac/ai/your_provider_client.py`
2. Inherit from `BaseAIClient`
3. Implement required methods
4. Add to `router.py` initialization
5. Update documentation

## License

Part of Isaac project - see main LICENSE file.
