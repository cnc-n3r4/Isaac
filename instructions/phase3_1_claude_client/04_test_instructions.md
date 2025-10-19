# Test Instructions: Claude API Client

## Goal
Verify ClaudeClient works with real API and handles errors gracefully.

**Time Estimate:** 30 minutes

---

## Prerequisites

**1. API Key Setup**

Edit `~/.isaac/config.json`:
```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-api03-...",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```

**Get API key from:** https://console.anthropic.com/

---

## Manual Tests

### Test 1: Import Check

```bash
python -c "from isaac.ai.claude_client import ClaudeClient; print('✅ Import successful')"
```

**Expected:** `✅ Import successful`

---

### Test 2: Instantiation

```python
from isaac.ai.claude_client import ClaudeClient
client = ClaudeClient('test-key')
print(f'✅ Client created: {client.model}')
```

**Expected:** `✅ Client created: claude-sonnet-4-5-20250929`

---

### Test 3: Translation (Requires Valid API Key)

```python
from isaac.ai.claude_client import ClaudeClient
import json

# Load API key from config
import os
config_path = os.path.expanduser('~/.isaac/config.json')
with open(config_path) as f:
    config = json.load(f)

client = ClaudeClient(config['claude_api_key'])
result = client.translate_to_shell('find large files', 'bash')

print(f"Success: {result.get('success')}")
print(f"Command: {result.get('command')}")
print(f"Explanation: {result.get('explanation')}")
print(f"Confidence: {result.get('confidence')}")
```

**Expected Output:**
```
Success: True
Command: find . -type f -size +100M
Explanation: Finds files larger than 100MB in current directory
Confidence: 0.9
```

---

### Test 4: Validation

```python
client = ClaudeClient(api_key)  # Use your API key
result = client.validate_command('rm -rf /', 'bash')

print(f"Safe: {result['safe']}")
print(f"Warnings: {result['warnings']}")
print(f"Suggestions: {result['suggestions']}")
```

**Expected Output:**
```
Safe: False
Warnings: ['Will delete entire filesystem', 'Catastrophic data loss']
Suggestions: ['Never run this command', 'Use rm with specific paths only']
```

---

### Test 5: Typo Correction

```python
client = ClaudeClient(api_key)
result = client.correct_typo('grp pattern file.txt', 'bash')

print(f"Original: {result['original']}")
print(f"Corrected: {result['corrected']}")
print(f"Confidence: {result['confidence']}")
```

**Expected Output:**
```
Original: grp pattern file.txt
Corrected: grep pattern file.txt
Confidence: 0.95
```

---

### Test 6: Task Planning

```python
client = ClaudeClient(api_key)
result = client.plan_task('backup my home folder to external drive', 'bash')

print(f"Success: {result['success']}")
print(f"Steps: {len(result['steps'])}")
for i, step in enumerate(result['steps'], 1):
    print(f"  {i}. [{step['tier']}] {step['command']}")
print(f"Duration: {result['estimated_duration']}")
print(f"Risks: {result['risks']}")
```

**Expected Output:**
```
Success: True
Steps: 3
  1. [1] cd ~
  2. [2] tar -czf /mnt/external/home_backup.tar.gz .
  3. [1] ls -lh /mnt/external/home_backup.tar.gz
Duration: 5-10 minutes
Risks: ['Large file transfer', 'Disk space required']
```

---

## Error Handling Tests

### Test 7: Invalid API Key

```python
client = ClaudeClient('sk-ant-invalid-key')
result = client.translate_to_shell('list files', 'bash')

print(f"Success: {result['success']}")
print(f"Error: {result.get('error')}")
```

**Expected:**
```
Success: False
Error: API error: 401
```

---

### Test 8: Network Timeout

```python
# Temporarily set timeout to 1 second
client = ClaudeClient(api_key)
client.timeout = 1  # Very short timeout

result = client.plan_task('complex multi-step task...', 'bash')
print(f"Error: {result.get('error')}")
```

**Expected:** `Error: API timeout (10 seconds)` or successful response

---

### Test 9: No Network Connection

```python
# Disconnect network, then run
client = ClaudeClient(api_key)
result = client.translate_to_shell('test', 'bash')

print(f"Success: {result['success']}")
print(f"Error: {result['error']}")
```

**Expected:**
```
Success: False
Error: Network connection failed
```

---

## Automated Tests (Optional)

If pytest installed:

```python
# tests/test_claude_client.py
import pytest
from isaac.ai.claude_client import ClaudeClient

def test_client_initialization():
    client = ClaudeClient('test-key')
    assert client.api_key == 'test-key'
    assert client.model == 'claude-sonnet-4-5-20250929'
    assert client.timeout == 10

def test_translate_to_shell_structure():
    # Test with mock (no actual API call)
    client = ClaudeClient('test-key')
    # Mock _call_api to return test data
    # ... (requires pytest-mock)
```

**Run tests:**
```bash
pytest tests/test_claude_client.py -v
```

---

## Success Criteria

✅ **All tests must pass:**
- [ ] Import successful
- [ ] Client instantiates
- [ ] Translation returns valid command (with API key)
- [ ] Validation returns safety info
- [ ] Typo correction works
- [ ] Task planning returns steps
- [ ] Error handling graceful (no crashes)
- [ ] Invalid API key handled
- [ ] Network errors handled

---

## Troubleshooting

**Issue:** `ModuleNotFoundError: No module named 'requests'`
**Solution:** `pip install requests`

**Issue:** `401 Unauthorized from API`
**Solution:** Check API key in ~/.isaac/config.json, verify it's valid

**Issue:** `Timeout errors`
**Solution:** Check network, try increasing client.timeout = 30

**Issue:** `JSONDecodeError`
**Solution:** Claude's response wasn't valid JSON. Check prompt formatting in code.

**Issue:** `KeyError in response parsing`
**Solution:** Claude's JSON structure different than expected. Add .get() with defaults.

---

**END OF TEST INSTRUCTIONS**
