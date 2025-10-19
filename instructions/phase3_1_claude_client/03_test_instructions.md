# Test Instructions: Claude API Client

## Goal
Verify ClaudeClient class works correctly with Claude API.

**Time Estimate:** 15 minutes

---

## Prerequisites

**API Key Required:**
- Obtain Claude API key from: https://console.anthropic.com/
- Format: `sk-ant-...`
- Add to `~/.isaac/config.json`:

```json
{
  "ai_enabled": true,
  "claude_api_key": "sk-ant-YOUR_KEY_HERE",
  "ai_model": "claude-sonnet-4-5-20250929"
}
```

---

## Manual Test Script

**File:** `test_claude_manual.py` (temporary, don't commit)

```python
#!/usr/bin/env python3
"""Manual test for ClaudeClient"""

import sys
sys.path.insert(0, '.')  # Add current dir to path

from isaac.ai.claude_client import ClaudeClient

# Initialize (use your API key)
print("Initializing ClaudeClient...")
client = ClaudeClient(api_key="sk-ant-YOUR_KEY_HERE")

print("\n" + "="*60)
print("TEST 1: Translation")
print("="*60)
result = client.translate_to_shell("find large files", "bash")
if result.get('success'):
    print(f"✅ Command: {result['command']}")
    print(f"   Explanation: {result['explanation']}")
    print(f"   Confidence: {result['confidence']}")
else:
    print(f"❌ Error: {result['error']}")

print("\n" + "="*60)
print("TEST 2: Validation")
print("="*60)
result = client.validate_command("rm -rf /tmp/test", "bash")
print(f"Safe: {result['safe']}")
print(f"Warnings: {result['warnings']}")
print(f"Suggestions: {result['suggestions']}")

print("\n" + "="*60)
print("TEST 3: Typo Correction")
print("="*60)
result = client.correct_typo("grp pattern file.txt", "bash")
if result['corrected']:
    print(f"✅ Original: {result['original']}")
    print(f"   Corrected: {result['corrected']}")
    print(f"   Confidence: {result['confidence']}")
else:
    print(f"No typo detected")

print("\n" + "="*60)
print("TEST 4: Task Planning")
print("="*60)
result = client.plan_task("backup my documents folder", "bash")
if result.get('success'):
    print(f"✅ Steps: {len(result['steps'])}")
    for i, step in enumerate(result['steps'], 1):
        print(f"   {i}. [{step['tier']}] {step['command']}")
        print(f"      {step['description']}")
    print(f"   Duration: {result['estimated_duration']}")
    print(f"   Risks: {result['risks']}")
else:
    print(f"❌ Error: {result['error']}")

print("\n" + "="*60)
print("All tests complete!")
print("="*60)
```

---

## Running Tests

**Step 1: Add API key to script**
```bash
# Edit test_claude_manual.py, line 9
# Replace "sk-ant-YOUR_KEY_HERE" with your actual key
```

**Step 2: Run test**
```bash
cd C:\Projects\isaac
python test_claude_manual.py
```

**Expected Output:**
```
Initializing ClaudeClient...

============================================================
TEST 1: Translation
============================================================
✅ Command: find . -type f -size +100M
   Explanation: Finds files larger than 100MB
   Confidence: 0.95

============================================================
TEST 2: Validation
============================================================
Safe: True
Warnings: ['Will delete files in /tmp/test']
Suggestions: ['Use -i flag for confirmation']

============================================================
TEST 3: Typo Correction
============================================================
✅ Original: grp pattern file.txt
   Corrected: grep pattern file.txt
   Confidence: 0.9

============================================================
TEST 4: Task Planning
============================================================
✅ Steps: 3
   1. [1] cd ~/documents
      Navigate to documents folder
   2. [2] tar -czf backup.tar.gz .
      Create compressed archive
   3. [1] ls -lh backup.tar.gz
      Verify backup created
   Duration: 1-2 minutes
   Risks: ['Large file operation']

============================================================
All tests complete!
============================================================
```

---

## Error Scenarios to Test

**Test 1: Invalid API Key**
```python
client = ClaudeClient(api_key="invalid_key")
result = client.translate_to_shell("test", "bash")
# Should return: {'success': False, 'error': 'API error: 401'}
```

**Test 2: Network Timeout**
```python
# Disconnect internet, then run:
result = client.translate_to_shell("test", "bash")
# Should return: {'success': False, 'error': 'Network connection failed'}
```

**Test 3: No API Key**
```python
client = ClaudeClient(api_key="")
result = client.translate_to_shell("test", "bash")
# Should return error (handled gracefully, no exception)
```

---

## Automated Tests (pytest)

**Reference:** `tests/test_ai_integration.py`

**Run AI tests:**
```bash
pytest tests/test_ai_integration.py::test_claude_client_translate -v
pytest tests/test_ai_integration.py::test_claude_client_validate -v
pytest tests/test_ai_integration.py::test_claude_client_correct -v
pytest tests/test_ai_integration.py::test_claude_client_plan -v
```

**Expected:**
```
tests/test_ai_integration.py::test_claude_client_translate PASSED
tests/test_ai_integration.py::test_claude_client_validate PASSED
tests/test_ai_integration.py::test_claude_client_correct PASSED
tests/test_ai_integration.py::test_claude_client_plan PASSED
```

---

## Success Criteria

✅ **Phase 3.1 Complete When:**
- [ ] ClaudeClient class created (~230 lines)
- [ ] All 4 methods implemented and working
- [ ] Manual test script passes all 4 tests
- [ ] Error handling verified (invalid key, timeout, no network)
- [ ] No exceptions raised (all methods return dicts)
- [ ] API calls complete within 10-second timeout

---

## Troubleshooting

**Issue: "ModuleNotFoundError: No module named 'requests'"**
```bash
pip install requests --break-system-packages
```

**Issue: "API error: 401"**
- Check API key format (must start with `sk-ant-`)
- Verify key is valid at https://console.anthropic.com/

**Issue: "API timeout (10 seconds)"**
- Network slow or unstable
- Claude API may be overloaded
- Retry later

**Issue: "Failed to parse AI response"**
- Claude returned non-JSON text
- Retry request (usually transient)

---

## Next Phase

**After Phase 3.1 passes:**
- ✅ Claude API client working
- Ready for Phase 3.2: Natural Language Translation

---

**END OF TEST INSTRUCTIONS**
