# Deployment Guide: Isaac 2.0 MVP

## Goal
Complete deployment instructions for user: install Python package, upload PHP to GoDaddy, configure, and test multi-machine sync.

**Time Estimate:** 30 minutes (user execution time)

**Prerequisites:** 
- All Python files built by VSCode agent
- All PHP files built by VSCode agent
- GoDaddy hosting account with PHP support
- Python 3.8+ installed on all machines

---

## Phase 1: Install Python Package (Each Machine)

### Windows (PowerShell)

```powershell
# Navigate to isaac project directory
cd C:\path\to\isaac

# Install in development mode
pip install -e .

# Verify installation
isaac --help

# Expected: Help text displays
```

### Linux (bash)

```bash
# Navigate to isaac project directory
cd /path/to/isaac

# Install in development mode
pip install -e .

# Verify installation
isaac --help

# Expected: Help text displays
```

---

## Phase 2: Upload PHP API to GoDaddy

### Option A: cPanel File Manager

1. **Log in to GoDaddy cPanel**
   - URL: https://yourhosting.godaddy.com/cPanel
   - Enter credentials

2. **Navigate to File Manager**
   - Click "File Manager" icon
   - Go to `public_html/`

3. **Create API Directory**
   - Click "New Folder"
   - Name: `isaac`
   - Inside `isaac/`, create folder: `api`

4. **Upload PHP Files**
   - Navigate to `public_html/isaac/api/`
   - Click "Upload"
   - Select all 5 files from `php_api/` folder:
     - config.php
     - save_session.php
     - get_session.php
     - health_check.php
     - .htaccess

5. **Create Data Directory**
   - Inside `public_html/isaac/api/`, create folder: `data`
   - Right-click `data/` → Permissions → Set to `755`

### Option B: FTP (FileZilla/WinSCP)

1. **Connect to GoDaddy FTP**
   - Host: ftp.yourdomain.com
   - Username: Your FTP username
   - Password: Your FTP password
   - Port: 21

2. **Navigate to public_html/**
   - Create folder: `isaac/api/`

3. **Upload Files**
   - Drag all 5 PHP files from local `php_api/` to remote `public_html/isaac/api/`

4. **Create data/ folder**
   - Create folder: `public_html/isaac/api/data/`
   - Set permissions: 755

---

## Phase 3: Configure API

### Step 1: Generate Secure API Key

**Windows (PowerShell):**
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Linux (bash):**
```bash
openssl rand -hex 16
```

**Copy the output** (example: `a3f9d8e2c1b4567890abcdef12345678`)

### Step 2: Edit config.php on Server

**Via cPanel File Manager:**
1. Navigate to `public_html/isaac/api/config.php`
2. Right-click → Edit
3. Find line: `define('API_KEY', 'isaac_secure_key_CHANGE_THIS_2025');`
4. Replace with: `define('API_KEY', 'a3f9d8e2c1b4567890abcdef12345678');`
5. Save file

**Via FTP:**
1. Download `config.php`
2. Edit locally with text editor
3. Change API_KEY value
4. Upload back to server

### Step 3: Test API

**Test health check (no auth required):**
```bash
curl https://yourdomain.com/isaac/api/health_check.php
```

**Expected:**
```json
{
  "status": "online",
  "timestamp": "2025-10-18T16:00:00+00:00",
  "version": "2.0.0"
}
```

**If this fails:** Check URL, verify files uploaded correctly

---

## Phase 4: Configure Isaac (Each Machine)

### Step 1: Edit Config File

**Location:** `~/.isaac/config.json` (created on first run)

**Windows:** `C:\Users\YourName\.isaac\config.json`  
**Linux:** `/home/username/.isaac/config.json`

**Content:**
```json
{
  "machine_id": "AUTO-DETECTED-HOSTNAME",
  "auto_run_tier2": false,
  "tier_overrides": {},
  "api_url": "https://yourdomain.com/isaac/api",
  "api_key": "a3f9d8e2c1b4567890abcdef12345678"
}
```

**Edit:**
- `api_url`: Your GoDaddy domain + `/isaac/api`
- `api_key`: Same key from config.php

### Step 2: Run Isaac (First Time)

**Windows:**
```powershell
isaac --start
```

**Linux:**
```bash
isaac --start
```

**Expected:**
1. Splash screen (5.5 seconds)
2. Header appears
3. Prompt: `isaac> Ready.`
4. Status: `[OFFLINE]` (cloud sync in Phase 2)

---

## Phase 5: Test Basic Functionality

### Test 1: Tier 1 Commands (Instant)

```bash
user> ls
```

**Expected:** Directory listing appears immediately

```bash
user> pwd
```

**Expected:** Current directory path

```bash
user> cd /tmp
user> pwd
```

**Expected:** `/tmp` (or `C:\Temp` on Windows)

### Test 2: Tier 3 Commands (Confirm)

```bash
user> git status
```

**Expected:**
```
Isaac > Validate this command: git status? [y/N]: y
[git output]
```

### Test 3: Tier 4 Commands (Lockdown)

```bash
user> rm -rf test
```

**Expected:**
```
============================================================
⚠️  DESTRUCTIVE COMMAND WARNING ⚠️
============================================================
Command: rm -rf test

This command can cause data loss or system damage.
Type 'yes' (exactly) to proceed, or anything else to abort.
============================================================
Isaac > Proceed? no
Isaac > Aborted. (Type 'yes' exactly to execute Tier 4 commands)
```

### Test 4: History Logging

```bash
user> echo test
user> exit

# Then check history
isaac --show-log
```

**Expected:** List of commands with timestamps

---

## Phase 6: Multi-Machine Testing (MVP: Local Only)

**Note:** Cloud sync (PHP API integration) is in Phase 2. For MVP, each machine has independent local history.

### Test on Second Machine

1. **Install Isaac** (repeat Phase 1)
2. **Run:**
```bash
isaac --start
user> hostname
user> pwd
user> exit
```

3. **Check history:**
```bash
isaac --show-log
```

**Expected:** Only commands from THIS machine (no sync yet)

### Test Machines List

```bash
isaac --machines
```

**Expected:** List of all machines with command counts

---

## Phase 7: Verify Installation

### Checklist

**Python Package:**
- [ ] `pip list | grep isaac` shows isaac 2.0.0
- [ ] `isaac --help` displays help text
- [ ] `~/.isaac/` directory created
- [ ] `~/.isaac/config.json` exists

**GoDaddy PHP API:**
- [ ] All 5 PHP files uploaded to `public_html/isaac/api/`
- [ ] `data/` folder created with 755 permissions
- [ ] config.php edited with secure API key
- [ ] health_check.php returns `{"status":"online"}`

**Isaac Functionality:**
- [ ] Splash screen displays (5.5 seconds)
- [ ] Header appears with shell + machine name
- [ ] Tier 1 commands execute instantly
- [ ] Tier 3 commands prompt for confirmation
- [ ] Tier 4 commands show lockdown warning
- [ ] History logs commands
- [ ] `exit` quits cleanly

**Testing:**
- [ ] pytest runs successfully (all tests pass)
- [ ] Tier validator tests pass (100%)

---

## Troubleshooting

### Issue: `isaac: command not found`

**Solution:**
```bash
# Reinstall
pip uninstall isaac
pip install -e .
```

### Issue: `ModuleNotFoundError: No module named 'isaac'`

**Solution:**
```bash
# Ensure setup.py correct, reinstall
pip install -e .
```

### Issue: Splash screen doesn't show

**Solution:**
- Verify `isaac/data/splash_art.txt` exists
- Check file path in splash_screen.py

### Issue: Header scrolls away

**Solution:**
- ANSI escape codes issue
- Windows: Install colorama (`pip install colorama`)
- Verify terminal supports ANSI

### Issue: PHP API returns 401 Unauthorized

**Solution:**
- Check API key matches in:
  - `config.php` (server)
  - `~/.isaac/config.json` (local)

### Issue: PHP API returns 404 Not Found

**Solution:**
- Verify URL: `https://yourdomain.com/isaac/api/health_check.php`
- Check files uploaded to correct directory

### Issue: data/ folder permission denied

**Solution:**
```bash
# Via SSH
chmod 755 public_html/isaac/api/data

# Via cPanel: Right-click folder → Permissions → 755
```

---

## Success Criteria

### Minimum Viable Product (MVP) - Tonight:

✅ **Installation:**
- Isaac installed on at least 1 machine
- `isaac --start` launches successfully

✅ **Core Functionality:**
- Splash screen displays
- Header shows shell + machine
- Tier 1 executes instantly (ls, cd, pwd)
- Tier 3 prompts for confirmation (git, cp, mv)
- Tier 4 shows lockdown (rm -rf)
- History logs commands locally

✅ **Testing:**
- All pytest tests pass (30+ tests)
- Tier 4 safety tests pass (CRITICAL)

✅ **PHP API:**
- Files uploaded to GoDaddy
- health_check.php returns online status
- API key configured

### Phase 2 Goals (Future):

⬜ Cloud sync active (Python client integrated)
⬜ Multi-machine session roaming
⬜ AI integration (natural language)
⬜ Task mode (multi-step automation)
⬜ Learning engine (auto-fix patterns)

---

## Next Steps

**After MVP Success:**

1. **Test on multiple machines**
   - Windows desktop
   - Linux VM
   - Verify independent histories

2. **Phase 2 Planning**
   - Cloud sync client integration
   - AI API integration
   - Task mode design

3. **User Feedback**
   - Daily use for 1 week
   - Note pain points
   - Feature requests

4. **Documentation**
   - Create user guide
   - Add examples
   - Record demo video

---

## Contact & Support

**Issues:** https://github.com/yourusername/isaac/issues  
**Docs:** https://github.com/yourusername/isaac/wiki  
**Email:** your.email@example.com

---

**END OF DEPLOYMENT GUIDE**

**Status:** MVP deployment complete! 🎉

Isaac 2.0 is now running with:
- Multi-platform support (PowerShell + bash)
- 5-tier command safety system
- Local session management
- PHP API ready for Phase 2 cloud sync
