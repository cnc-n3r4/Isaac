# Implementation: Create CloudClient Class

## Goal
Create HTTP client for GoDaddy API to enable cloud sync of Isaac session data.

**Time Estimate:** 45 minutes

---

## File to Create

**Path:** `C:\Projects\isaac\isaac\api\cloud_client.py`

**Lines:** ~120

---

## Complete Implementation

```python
"""CloudClient - HTTP wrapper for GoDaddy session sync API."""

import requests
from typing import Optional


class CloudClient:
    """HTTP client for syncing Isaac session data to GoDaddy cloud API.
    
    All methods return False/None on errors (never raise exceptions).
    This ensures cloud failures don't crash Isaac.
    """
    
    def __init__(self, api_url: str, api_key: str, user_id: str):
        """Initialize CloudClient.
        
        Args:
            api_url: Base URL of GoDaddy API (e.g., https://n3r4.xyz/isaac/api)
            api_key: Authentication key for API
            user_id: Unique user identifier (e.g., "ndemi")
        """
        self.api_url = api_url.rstrip('/')  # Remove trailing slash
        self.api_key = api_key
        self.user_id = user_id
        self.timeout = 5  # seconds
    
    def health_check(self) -> bool:
        """Check if GoDaddy API is reachable.
        
        Returns:
            True if API responds with 200 OK, False otherwise
        """
        try:
            url = f"{self.api_url}/health_check.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('success', False)
            else:
                return False
                
        except Exception:
            # Network error, timeout, or malformed response
            return False
    
    def save_session_file(self, filename: str, data: dict) -> bool:
        """Save session file to cloud.
        
        Args:
            filename: Name of file (e.g., "preferences.json", "command_history.json")
            data: Dictionary to save
            
        Returns:
            True if saved successfully, False on error
        """
        try:
            url = f"{self.api_url}/save_session.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'user_id': self.user_id,
                'filename': filename,
                'data': data
            }
            
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
            else:
                return False
                
        except Exception:
            # Network error, timeout, or malformed response
            return False
    
    def get_session_file(self, filename: str) -> Optional[dict]:
        """Retrieve session file from cloud.
        
        Args:
            filename: Name of file to retrieve
            
        Returns:
            Dictionary if found, None if not found or on error
        """
        try:
            url = f"{self.api_url}/get_session.php"
            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }
            params = {
                'user_id': self.user_id,
                'filename': filename
            }
            
            response = requests.get(
                url, 
                headers=headers, 
                params=params, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('data')
            
            # Not found or error
            return None
                
        except Exception:
            # Network error, timeout, or malformed response
            return None
    
    def is_available(self) -> bool:
        """Check if cloud sync is currently available.
        
        Wrapper around health_check() for semantic clarity.
        
        Returns:
            True if cloud API is reachable, False otherwise
        """
        return self.health_check()
```

---

## Verification Steps

After creating the file:

### Check File Created
```bash
dir C:\Projects\isaac\isaac\api\cloud_client.py
```

**Expected:** File exists, ~120 lines

### Syntax Check
```bash
cd C:\Projects\isaac
python -m py_compile isaac/api/cloud_client.py
```

**Expected:** No syntax errors

### Import Test
```bash
python -c "from isaac.api.cloud_client import CloudClient; print('Import successful')"
```

**Expected:** "Import successful"

---

## Test Manually

### Test 1: Initialize CloudClient

```python
from isaac.api.cloud_client import CloudClient

# Initialize with test credentials
client = CloudClient(
    api_url='https://n3r4.xyz/isaac/api',
    api_key='isaac_demo_key_2024',
    user_id='test_user'
)

print(f"API URL: {client.api_url}")
print(f"User ID: {client.user_id}")
print(f"Timeout: {client.timeout}s")
```

**Expected Output:**
```
API URL: https://n3r4.xyz/isaac/api
User ID: test_user
Timeout: 5s
```

### Test 2: Health Check

```python
# Check if API is reachable
is_healthy = client.health_check()
print(f"API Health: {'OK' if is_healthy else 'UNREACHABLE'}")
```

**Expected Output:**
```
API Health: OK
```

**If UNREACHABLE:**
- Check network connectivity
- Verify API URL is correct
- Confirm GoDaddy API is deployed

### Test 3: Save Data

```python
# Save test preferences
test_data = {
    'auto_run': True,
    'theme': 'dark',
    'test_timestamp': '2025-10-19T12:00:00Z'
}

success = client.save_session_file('test_preferences.json', test_data)
print(f"Save Result: {'SUCCESS' if success else 'FAILED'}")
```

**Expected Output:**
```
Save Result: SUCCESS
```

**Verify on GoDaddy:**
- Check `public_html/isaac/api/data/test_user/test_preferences.json` exists
- File contains test_data

### Test 4: Retrieve Data

```python
# Get data back from cloud
retrieved = client.get_session_file('test_preferences.json')

if retrieved:
    print("Retrieved data:")
    print(f"  auto_run: {retrieved['auto_run']}")
    print(f"  theme: {retrieved['theme']}")
else:
    print("FAILED to retrieve")
```

**Expected Output:**
```
Retrieved data:
  auto_run: True
  theme: dark
```

### Test 5: Error Handling (Bad API Key)

```python
# Test with invalid credentials
bad_client = CloudClient(
    api_url='https://n3r4.xyz/isaac/api',
    api_key='INVALID_KEY',
    user_id='test_user'
)

# Should return False (not raise exception)
result = bad_client.health_check()
print(f"Bad key health check: {'PASSED' if not result else 'UNEXPECTED'}")
```

**Expected Output:**
```
Bad key health check: PASSED
```

**Important:** No exceptions raised, just returns False

---

## Common Pitfalls

⚠️ **Missing requests library**
- Problem: `ModuleNotFoundError: No module named 'requests'`
- Solution: `pip install requests --break-system-packages`

⚠️ **Trailing slash in api_url**
- Problem: URL becomes `https://n3r4.xyz/isaac/api//health_check.php` (double slash)
- Solution: `.rstrip('/')` in `__init__()` (already included)

⚠️ **Raising exceptions on errors**
- Problem: Cloud failure crashes Isaac
- Solution: All try/except blocks return False/None (already included)

⚠️ **Forgot Content-Type header**
- Problem: GoDaddy API returns 400 Bad Request
- Solution: `'Content-Type': 'application/json'` in save_session_file() (already included)

⚠️ **Timeout too long**
- Problem: Isaac freezes waiting for unresponsive API
- Solution: `timeout=5` (already set)

---

## Success Signals

✅ **File created:** `isaac/api/cloud_client.py`

✅ **No syntax errors**

✅ **Import works:** `from isaac.api.cloud_client import CloudClient`

✅ **Health check returns True** (if API online)

✅ **Save/get roundtrip works** (data saved and retrieved correctly)

✅ **Error handling tested** (bad credentials return False, not exception)

---

**END OF IMPLEMENTATION**
