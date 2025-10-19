# Implementation: PHP API for Cloud Sync

## Goal
Create PHP endpoints for GoDaddy cloud session storage (user uploads manually).

**Time Estimate:** 20 minutes

**Dependencies:** None (standalone PHP files)

---

## Overview

VSCode agent builds these files locally. User uploads to GoDaddy via FTP/cPanel.

**GoDaddy Structure:**
```
public_html/isaac/api/
├── config.php              (edit API_KEY before upload)
├── save_session.php
├── get_session.php
├── health_check.php
├── .htaccess
└── data/                   (create folder, chmod 755)
    └── [user_folders created automatically]
```

---

## File 1: config.php

**Path:** `php_api/config.php`

**Purpose:** API configuration, authentication, helper functions.

**Complete Implementation:**

```php
<?php
/**
 * Isaac API Configuration
 * Edit API_KEY before uploading to GoDaddy.
 */

// API Key for authentication
define('API_KEY', 'isaac_secure_key_CHANGE_THIS_2025');

// Data directory (relative to this file)
define('DATA_DIR', __DIR__ . '/data/');

// Allowed session files
define('ALLOWED_FILES', [
    'preferences.json',
    'command_history.json',
    'aiquery_history.json',
    'task_history.json',
    'learned_autofixes.json',
    'learned_patterns.json'
]);

/**
 * Validate API key from Authorization header.
 * Returns true if valid, sends 401 and exits if invalid.
 */
function validate_api_key($headers) {
    $auth_header = $headers['Authorization'] ?? '';
    
    if ($auth_header !== 'Bearer ' . API_KEY) {
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Unauthorized']);
        exit;
    }
}

/**
 * Validate filename is in allowed list.
 * Returns true if valid, sends 400 and exits if invalid.
 */
function validate_filename($filename) {
    if (!in_array($filename, ALLOWED_FILES)) {
        http_response_code(400);
        header('Content-Type: application/json');
        echo json_encode(['error' => 'Invalid filename']);
        exit;
    }
}

/**
 * Get or create user directory.
 * Returns path to user's data folder.
 */
function get_user_dir($user_id) {
    // Sanitize user_id
    $user_id = preg_replace('/[^a-zA-Z0-9_-]/', '_', $user_id);
    
    $user_dir = DATA_DIR . $user_id . '/';
    
    if (!is_dir($user_dir)) {
        mkdir($user_dir, 0755, true);
    }
    
    return $user_dir;
}
?>
```

---

## File 2: save_session.php

**Path:** `php_api/save_session.php`

**Purpose:** Save session file (POST endpoint).

**Complete Implementation:**

```php
<?php
/**
 * Save Session Endpoint
 * POST https://yourdomain.com/isaac/api/save_session.php
 * 
 * Headers:
 *   Authorization: Bearer {API_KEY}
 *   Content-Type: application/json
 * 
 * Body:
 *   {
 *     "user_id": "string",
 *     "filename": "preferences.json",
 *     "data": {...}
 *   }
 */

require_once 'config.php';

header('Content-Type: application/json');

// Validate authentication
$headers = getallheaders();
validate_api_key($headers);

// Parse request body
$input = json_decode(file_get_contents('php://input'), true);

if (!isset($input['user_id'], $input['filename'], $input['data'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required fields']);
    exit;
}

$user_id = $input['user_id'];
$filename = $input['filename'];
$data = $input['data'];

// Validate filename
validate_filename($filename);

// Get user directory
$user_dir = get_user_dir($user_id);
$file_path = $user_dir . $filename;

// Save data
file_put_contents($file_path, json_encode($data, JSON_PRETTY_PRINT));

// Response
echo json_encode([
    'success' => true,
    'message' => 'Session saved',
    'timestamp' => date('c')
]);
?>
```

---

## File 3: get_session.php

**Path:** `php_api/get_session.php`

**Purpose:** Retrieve session file (GET endpoint).

**Complete Implementation:**

```php
<?php
/**
 * Get Session Endpoint
 * GET https://yourdomain.com/isaac/api/get_session.php?user_id=X&filename=Y
 * 
 * Headers:
 *   Authorization: Bearer {API_KEY}
 * 
 * Query Params:
 *   user_id: User identifier
 *   filename: preferences.json | command_history.json | etc.
 */

require_once 'config.php';

header('Content-Type: application/json');

// Validate authentication
$headers = getallheaders();
validate_api_key($headers);

// Get parameters
if (!isset($_GET['user_id'], $_GET['filename'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing parameters']);
    exit;
}

$user_id = $_GET['user_id'];
$filename = $_GET['filename'];

// Validate filename
validate_filename($filename);

// Get user directory
$user_dir = get_user_dir($user_id);
$file_path = $user_dir . $filename;

// Check if file exists
if (!file_exists($file_path)) {
    // Return empty structure for new users
    echo json_encode([]);
    exit;
}

// Read and return file
$data = json_decode(file_get_contents($file_path), true);
echo json_encode($data);
?>
```

---

## File 4: health_check.php

**Path:** `php_api/health_check.php`

**Purpose:** API status endpoint (no auth required).

**Complete Implementation:**

```php
<?php
/**
 * Health Check Endpoint
 * GET https://yourdomain.com/isaac/api/health_check.php
 * 
 * No authentication required - used to verify API is online.
 */

header('Content-Type: application/json');

echo json_encode([
    'status' => 'online',
    'timestamp' => date('c'),
    'version' => '2.0.0'
]);
?>
```

---

## File 5: .htaccess

**Path:** `php_api/.htaccess`

**Purpose:** Security rules and HTTPS redirect.

**Complete Implementation:**

```apache
# Isaac API Security Rules

# Block direct access to config.php
<Files "config.php">
    Require all denied
</Files>

# Block access to data directory
<DirectoryMatch "data">
    Require all denied
</DirectoryMatch>

# Force HTTPS (if available)
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{HTTPS} off
    RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
</IfModule>

# Enable CORS (for local testing)
<IfModule mod_headers.c>
    Header set Access-Control-Allow-Origin "*"
    Header set Access-Control-Allow-Methods "GET, POST, OPTIONS"
    Header set Access-Control-Allow-Headers "Authorization, Content-Type"
</IfModule>
```

---

## Deployment Instructions (For User)

### Step 1: Upload Files to GoDaddy

**Via cPanel File Manager:**
1. Log in to GoDaddy cPanel
2. Navigate to File Manager
3. Go to `public_html/`
4. Create folder: `isaac/api/`
5. Upload all 5 PHP files to `public_html/isaac/api/`

**Via FTP (FileZilla/WinSCP):**
1. Connect to GoDaddy FTP
2. Navigate to `public_html/`
3. Create folder: `isaac/api/`
4. Upload all 5 files

---

### Step 2: Create Data Directory

**In cPanel File Manager:**
1. Go to `public_html/isaac/api/`
2. Create folder: `data/`
3. Set permissions: 755 (read/write/execute for owner)

**Via SSH (if available):**
```bash
mkdir public_html/isaac/api/data
chmod 755 public_html/isaac/api/data
```

---

### Step 3: Configure API Key

**Edit config.php:**
1. Open `public_html/isaac/api/config.php`
2. Find line: `define('API_KEY', 'isaac_secure_key_CHANGE_THIS_2025');`
3. Change to secure random key: `define('API_KEY', 'your_random_32_char_key_here');`
4. Save file

**Generate secure key:**
```bash
# Linux/macOS
openssl rand -hex 16

# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

---

### Step 4: Test API

**Test health check (no auth):**
```bash
curl https://yourdomain.com/isaac/api/health_check.php
```

**Expected:**
```json
{
  "status": "online",
  "timestamp": "2025-10-18T15:00:00+00:00",
  "version": "2.0.0"
}
```

**Test save session (with auth):**
```bash
curl -X POST https://yourdomain.com/isaac/api/save_session.php \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "filename": "preferences.json",
    "data": {"machine_id": "TEST"}
  }'
```

**Expected:**
```json
{
  "success": true,
  "message": "Session saved",
  "timestamp": "2025-10-18T15:00:00+00:00"
}
```

**Test get session:**
```bash
curl "https://yourdomain.com/isaac/api/get_session.php?user_id=test_user&filename=preferences.json" \
  -H "Authorization: Bearer your_api_key_here"
```

**Expected:**
```json
{"machine_id": "TEST"}
```

---

## Verification Steps

### 1. Check Files Built Locally
```bash
ls php_api/
```

**Expected:**
```
config.php
save_session.php
get_session.php
health_check.php
.htaccess
```

### 2. Check PHP Syntax (Local)
```bash
php -l php_api/config.php
php -l php_api/save_session.php
php -l php_api/get_session.php
php -l php_api/health_check.php
```

**Expected:** `No syntax errors detected`

### 3. Test Locally (Optional - Requires PHP)
```bash
cd php_api
php -S localhost:8000

# In another terminal:
curl http://localhost:8000/health_check.php
```

---

## Common Pitfalls

⚠️ **data/ folder not writable**
- **Symptom:** `file_put_contents(): failed to open stream: Permission denied`
- **Fix:** `chmod 755 data/` on server

⚠️ **config.php accessible directly**
- **Symptom:** Security risk, API key exposed
- **Fix:** Verify .htaccess blocks access to config.php

⚠️ **CORS errors (browser testing)**
- **Symptom:** Browser blocks API calls
- **Fix:** Ensure CORS headers in .htaccess

⚠️ **401 Unauthorized**
- **Symptom:** API calls fail with 401
- **Fix:** Check API key matches in config.php and Python client

⚠️ **File not found errors**
- **Symptom:** `get_session.php` returns 404
- **Fix:** Verify files uploaded to correct path

---

## Success Signals

✅ All 5 PHP files created locally  
✅ PHP syntax validates (no errors)  
✅ Files uploaded to GoDaddy  
✅ data/ folder created with 755 permissions  
✅ config.php edited with secure API key  
✅ health_check.php returns `{"status":"online"}`  
✅ save_session.php accepts POST requests  
✅ get_session.php returns saved data  
✅ .htaccess blocks direct config.php access  
✅ Ready for next step (Testing)

---

**Next Step:** 10_impl_tests.md (Create pytest tests for tier_validator)

---

**END OF PHP API IMPLEMENTATION**
