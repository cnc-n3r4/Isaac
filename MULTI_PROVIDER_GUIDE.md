# Multi-Provider AI Support - Configuration Guide

**Updated:** 2025-10-19  
**Isaac Version:** 2.0.0

---

## 🎯 WHAT CHANGED

Isaac now supports **multiple AI providers** with automatic format detection:

- ✅ **Claude/Anthropic** (original)
- ✅ **OpenAI** (GPT-4, GPT-3.5, etc.)
- ✅ **Custom/Compatible APIs** (OpenRouter, local LLMs, etc.)

**No more hardcoded Claude-specific headers!**

---

## 🔧 CONFIG OPTIONS

### Anthropic Claude (Official)

```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-YOUR-KEY",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```

**Auto-detected as Claude** - Uses Anthropic headers automatically.

---

### OpenAI (GPT-4, GPT-3.5-turbo)

```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-YOUR-OPENAI-KEY",
  "claude_api_url": "https://api.openai.com/v1/chat/completions",
  "ai_model": "gpt-4",
  "ai_provider": "openai"
}
```

**Key differences:**
- ✅ Uses `Authorization: Bearer` header (not `x-api-key`)
- ✅ NO `anthropic-version` header
- ✅ Response format: `choices[0].message.content`
- ✅ Auto-detected from URL or model name

---

### OpenRouter (Multi-Model Gateway)

```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-or-v1-YOUR-KEY",
  "claude_api_url": "https://openrouter.ai/api/v1/chat/completions",
  "ai_model": "anthropic/claude-3-sonnet",
  "ai_provider": "openai"
}
```

**Works with OpenAI format!**

---

### Local LLM (LM Studio, Ollama, Text-generation-webui)

```json
{
  "ai_enabled": true,
  "claude_api_key": "not-needed-for-local",
  "claude_api_url": "http://localhost:1234/v1/chat/completions",
  "claude_timeout": 60,
  "ai_model": "local-model-name",
  "ai_provider": "openai"
}
```

**Most local LLMs use OpenAI-compatible format.**

---

### Custom/Unknown Provider

```json
{
  "ai_enabled": true,
  "claude_api_key": "your-key",
  "claude_api_url": "https://custom-api.com/v1/completions",
  "ai_model": "custom-model",
  "ai_provider": "custom"
}
```

**Auto-detection:**
- Sends BOTH `x-api-key` AND `Authorization: Bearer` headers
- Tries BOTH Claude and OpenAI response formats
- Works with most compatible APIs

---

## 🔍 AUTO-DETECTION LOGIC

### Provider is auto-detected if not specified:

**Detected as 'claude':**
- URL contains `anthropic.com`, OR
- Model name contains `claude`

**Detected as 'openai':**
- URL contains `openai.com`, OR  
- Model name contains `gpt`

**Otherwise:** `custom` (tries both formats)

---

## 📋 COMPLETE CONFIG REFERENCE

### All Available Options

```json
{
  "_comment": "Cloud sync (optional)",
  "sync_enabled": false,
  "api_url": "",
  "api_key": "",
  "user_id": "",

  "_comment": "AI features",
  "ai_enabled": true,
  "claude_api_key": "YOUR-API-KEY",
  "claude_api_url": "https://api.anthropic.com/v1/messages",
  "claude_api_version": "2023-06-01",
  "claude_timeout": 10,
  "ai_model": "claude-sonnet-4-5-20250929",
  "ai_provider": "claude",

  "_comment": "Feature toggles",
  "task_mode_enabled": true,
  "auto_correct_tier2": true,
  "ai_min_confidence": 0.7
}
```

### Option Descriptions

| Option | Required? | Used For | Notes |
|--------|-----------|----------|-------|
| `claude_api_key` | ✅ YES | All providers | Auth key |
| `claude_api_url` | Optional | Custom endpoints | Auto: Claude official |
| `claude_api_version` | Optional | Claude only | Ignored for OpenAI |
| `claude_timeout` | Optional | All providers | Default: 10 seconds |
| `ai_model` | Optional | All providers | Model identifier |
| `ai_provider` | Optional | All providers | 'claude', 'openai', 'custom' |

---

## 🎯 PROVIDER-SPECIFIC EXAMPLES

### Example 1: Pure Claude
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-...",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```
**Headers sent:**
- `x-api-key: sk-ant-api03-...`
- `anthropic-version: 2023-06-01`

**Response parsed from:** `data['content'][0]['text']`

---

### Example 2: Pure OpenAI
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-...",
  "claude_api_url": "https://api.openai.com/v1/chat/completions",
  "ai_model": "gpt-4"
}
```
**Headers sent:**
- `Authorization: Bearer sk-...`

**Response parsed from:** `data['choices'][0]['message']['content']`

---

### Example 3: Mixed (OpenRouter with Claude model)
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-or-v1-...",
  "claude_api_url": "https://openrouter.ai/api/v1/chat/completions",
  "ai_model": "anthropic/claude-3-sonnet",
  "ai_provider": "openai"
}
```
**Why specify provider?**
- Model name has "claude" → would auto-detect as "claude"
- But OpenRouter uses OpenAI format
- Explicit `"ai_provider": "openai"` overrides detection

---

## 🧪 TESTING

### Test Auto-Detection

**Test 1: Claude Auto-Detect**
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-...",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```
✅ Should detect as `claude` provider

---

**Test 2: OpenAI Auto-Detect**
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-...",
  "claude_api_url": "https://api.openai.com/v1/chat/completions",
  "ai_model": "gpt-4"
}
```
✅ Should detect as `openai` provider

---

**Test 3: Custom Provider**
```json
{
  "ai_enabled": true,
  "claude_api_key": "key",
  "claude_api_url": "https://my-api.com/v1/chat",
  "ai_model": "custom-model"
}
```
✅ Should detect as `custom` (tries both formats)

---

## 🔧 TROUBLESHOOTING

### "Response parsing error"

**Cause:** API response doesn't match Claude OR OpenAI format

**Solution:**
1. Check your API's response format
2. Try setting `ai_provider` explicitly
3. Custom APIs must return either:
   - Claude format: `{"content": [{"text": "..."}]}`
   - OpenAI format: `{"choices": [{"message": {"content": "..."}}]}`

---

### "API error: 401"

**OpenAI users:**
- Make sure `claude_api_url` points to OpenAI
- Verify key starts with `sk-` (not `sk-ant-`)

**Claude users:**
- Verify key starts with `sk-ant-api03-`
- Check key is valid at console.anthropic.com

---

### "API timeout"

**Local LLM users:**
- Increase timeout: `"claude_timeout": 60`
- Check local server is running
- Test with: `curl http://localhost:1234/v1/models`

---

## 📊 COMPARISON TABLE

| Feature | Claude | OpenAI | Custom |
|---------|--------|--------|--------|
| Header Format | `x-api-key` | `Authorization` | Both |
| Version Header | ✅ Required | ❌ N/A | Optional |
| Response Format | `content[0].text` | `choices[0].message.content` | Auto-detect |
| Auto-Detection | URL/model | URL/model | Fallback |
| Official Docs | docs.anthropic.com | platform.openai.com | Varies |

---

## ✅ MIGRATION GUIDE

### From Pure Claude → Multi-Provider

**Old config (still works!):**
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-...",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```

**New capabilities (add if switching):**
```json
{
  "ai_enabled": true,
  "claude_api_key": "NEW-PROVIDER-KEY",
  "claude_api_url": "NEW-PROVIDER-URL",
  "ai_model": "NEW-MODEL",
  "ai_provider": "openai"
}
```

**No breaking changes - old configs work unchanged!**

---

## 🚀 QUICK RECIPES

### Use OpenAI for translation, Claude for validation
**Not yet supported** - single provider per session.  
Future: Per-feature provider selection.

### Switch between providers
Edit `~/.isaac/config.json` and restart Isaac.

### Test without API key
Use local LLM with `"claude_api_key": "not-needed"`

---

## 📝 SUMMARY

**What's new:**
- ✅ OpenAI support (GPT-4, GPT-3.5)
- ✅ Auto-detection based on URL/model
- ✅ Custom provider support
- ✅ Flexible header/response handling
- ✅ NO breaking changes

**What's required:**
- ✅ `claude_api_key` (always)
- ✅ `claude_api_url` (if not Anthropic)
- ✅ `ai_provider` (optional, auto-detected)

**What's optional:**
- `claude_api_version` (Claude only)
- `claude_timeout` (all providers)
- `ai_model` (provider-specific default)

---

**File:** MULTI_PROVIDER_GUIDE.md  
**Isaac Version:** 2.0.0  
**Status:** ✅ Production Ready
