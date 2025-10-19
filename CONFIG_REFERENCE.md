# Isaac 2.0 - Configuration Guide

## 📋 Complete Configuration Reference

Location: `~/.isaac/config.json` (or `C:\Users\USERNAME\.isaac\config.json` on Windows)

---

## 🎯 Full Configuration Example

```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_prod_a8f3k2m9x7q4w1p5z6n8v2c3b7",
  "user_id": "ndemi",
  "ai_enabled": true,
  "claude_api_key": "xai-UDuUicTFELExGh86kIifPbh4FVWzrU8rDB23wt3w0mFRMaJQXNetRH8RaiKmNtNxnBHMMy2b4le2OP7L",
  "claude_api_url": "https://api.x.ai/v1/chat/completions",
  "ai_model": "grok-4-fast-reasoning",
  "ai_provider": "openai",              // ← ADD THIS
  "claude_timeout": 10,
  "task_mode_enabled": true,
  "auto_correct_tier2": true,
  "ai_min_confidence": 0.7
}
```

---

## 🔧 Configuration Options

### Cloud Sync Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sync_enabled` | boolean | `false` | Enable multi-machine cloud sync |
| `api_url` | string | - | GoDaddy API endpoint URL |
| `api_key` | string | - | GoDaddy API authentication key |
| `user_id` | string | - | Your unique user identifier |

**Example (Cloud Sync Enabled):**
```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_prod_a8f3k2m9x7q4w1p5z6n8v2c3b7",
  "user_id": "ndemi"
}
```

**Example (Cloud Sync Disabled):**
```json
{
  "sync_enabled": false
}
```

---

### AI Settings (Claude API)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ai_enabled` | boolean | `false` | Enable AI features |
| `claude_api_key` | string | - | Anthropic API key (required for AI) |
| `claude_api_url` | string | `https://api.anthropic.com/v1/messages` | Claude API endpoint |
| `claude_api_version` | string | `2023-06-01` | API version header |
| `claude_timeout` | integer | `10` | API timeout in seconds |
| `ai_model` | string | `claude-sonnet-4-5-20250929` | Claude model to use |
| `task_mode_enabled` | boolean | `true` | Enable multi-step task automation |
| `auto_correct_tier2` | boolean | `true` | Auto-correct typos in Tier 2 commands |
| `ai_min_confidence` | float | `0.7` | Minimum confidence for AI translations (0.0-1.0) |

**Example (Official Anthropic API):**
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-YOUR-KEY-HERE"
}
```

**Example (Custom API Endpoint):**
```json
{
  "ai_enabled": true,
  "claude_api_key": "YOUR-API-KEY",
  "claude_api_url": "https://your-proxy.com/v1/chat/completions",
  "claude_api_version": "2024-01-01",
  "claude_timeout": 30
}
```

---

## 🚀 Quick Start Configurations

### Minimal (Local Only, No AI)
```json
{}
```
Basic Isaac MVP with 5-tier safety system.

---

### AI Only (No Cloud Sync)
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-YOUR-KEY-HERE"
}
```
All AI features, local storage only.

---

### Cloud Sync Only (No AI)
```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_prod_a8f3k2m9x7q4w1p5z6n8v2c3b7",
  "user_id": "ndemi"
}
```
Multi-machine sync, no AI features.

---

### Full Featured (Cloud + AI)
```json
{
  "sync_enabled": true,
  "api_url": "https://n3r4.xyz/isaac/api",
  "api_key": "isaac_prod_a8f3k2m9x7q4w1p5z6n8v2c3b7",
  "user_id": "ndemi",
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-YOUR-KEY-HERE",
  "ai_model": "claude-sonnet-4-5-20250929",
  "task_mode_enabled": true
}
```
Everything Isaac 2.0 offers!

---

## 🔌 Custom API Endpoints

### OpenAI-Compatible APIs

If you're using an OpenAI-compatible endpoint (e.g., OpenRouter, local LLM), you can configure it like this:

```json
{
  "ai_enabled": true,
  "claude_api_key": "YOUR-API-KEY",
  "claude_api_url": "https://openrouter.ai/api/v1/chat/completions",
  "claude_api_version": "2023-06-01",
  "ai_model": "anthropic/claude-3-sonnet"
}
```

**Note:** The endpoint must accept Claude's message format:
- Headers: `x-api-key`, `anthropic-version`, `content-type`
- Payload: `model`, `max_tokens`, `temperature`, `messages`
- Response: `content[0]['text']`

---

### Local LLM (LM Studio, Ollama, etc.)

```json
{
  "ai_enabled": true,
  "claude_api_key": "not-needed-for-local",
  "claude_api_url": "http://localhost:1234/v1/messages",
  "claude_timeout": 60,
  "ai_model": "local-model-name"
}
```

**Note:** Your local LLM server must implement Claude's API format or use a proxy/adapter.

---

## 🛡️ Security Best Practices

### Protect Your API Keys

**DO:**
- ✅ Keep config.json in `~/.isaac/` (user-only access)
- ✅ Add `config.json` to `.gitignore`
- ✅ Use environment-specific keys (dev vs prod)
- ✅ Rotate keys periodically

**DON'T:**
- ❌ Commit config.json to version control
- ❌ Share API keys in screenshots/logs
- ❌ Use production keys in development
- ❌ Store keys in plain text in public repos

---

### File Permissions

**Linux/Mac:**
```bash
chmod 600 ~/.isaac/config.json
```

**Windows:**
```powershell
# File is already user-only in %USERPROFILE%\.isaac\
```

---

## 🧪 Testing Your Configuration

### Verify Config Loaded
```bash
python -m isaac
# Look for: "Isaac > Loaded from local storage."
# or "Isaac > Loaded preferences from cloud."
```

### Test Cloud Sync
```bash
# On machine 1:
isaac
ls  # Run a command
exit

# On machine 2:
isaac
# Should see command history from machine 1
```

### Test AI Features
```bash
isaac backup my documents folder
# Should translate to tar/zip command

ls /usrbin  # Typo
# Should auto-correct to /usr/bin

rm -rf /tmp
# Should show AI safety warnings
```

---

## 🔍 Troubleshooting

### "Cloud sync unavailable"
- Check `api_url` is correct
- Verify `api_key` matches PHP config
- Test API: `curl https://your-api-url/health_check.php`

### "Claude API key not configured"
- Ensure `claude_api_key` is set
- Verify key starts with `sk-ant-api03-`
- Check key is valid at console.anthropic.com

### "AI validation unavailable"
- Check `ai_enabled: true`
- Verify API endpoint is reachable
- Test with: `curl -I https://api.anthropic.com`

---

## 📝 Configuration Template

Save this as `~/.isaac/config.json`:

```json
{
  "_comment_sync": "Cloud sync settings (optional)",
  "sync_enabled": false,
  "api_url": "",
  "api_key": "",
  "user_id": "",

  "_comment_ai": "AI features (optional)",
  "ai_enabled": false,
  "claude_api_key": "",
  "claude_api_url": "https://api.anthropic.com/v1/messages",
  "claude_api_version": "2023-06-01",
  "claude_timeout": 10,
  "ai_model": "claude-sonnet-4-5-20250929",

  "_comment_features": "Feature toggles",
  "task_mode_enabled": true,
  "auto_correct_tier2": true,
  "ai_min_confidence": 0.7
}
```

---

## 🎉 Ready to Use!

1. Copy the template above
2. Edit `~/.isaac/config.json`
3. Add your API keys
4. Save and start Isaac
5. Test features

**For more help:** Check the completion reports in `instructions/from-agent/`

---

**File:** CONFIG_REFERENCE.md  
**Updated:** 2025-10-19  
**Isaac Version:** 2.0.0
