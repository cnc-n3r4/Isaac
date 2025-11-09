# Isaac Cross-Platform Development Setup

## Windows Access to NAS

### Step 1: Map Network Drive

**Via File Explorer:**
1. Open File Explorer
2. Click "This PC" → "Map network drive"
3. Choose drive letter (e.g., Z:)
4. Enter path: `\\ls220d759\share\ISAAC` or `\\192.168.12.10\share\ISAAC`
5. Check "Reconnect at sign-in"
6. Enter credentials if prompted
7. Click "Finish"

**Via Command Line (Run as Administrator):**
```cmd
net use Z: \\192.168.12.10\share\ISAAC /persistent:yes
```

**Result:** Isaac project available at `Z:\` (or your chosen drive letter)

---

### Step 2: Install Python on Windows

1. Download Python 3.10+ from https://www.python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

---

### Step 3: Setup Virtual Environment

Open PowerShell or Command Prompt:

```powershell
# Navigate to project
cd Z:\

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 4: Configure API Keys

**Option A: Environment Variables (Recommended)**

Open PowerShell as Administrator:
```powershell
# Set API keys permanently
[Environment]::SetEnvironmentVariable("XAI_API_KEY", "your-key", "User")
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key", "User")
[Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "your-key", "User")
```

**Option B: .env File**

Create `Z:\.env`:
```
XAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
OPENAI_API_KEY=your-key
```

---

### Step 5: Setup Claude Code (Windows)

1. Install Claude Code for Windows from https://claude.com/claude-code
2. Open Claude Code
3. Open folder: `Z:\` (your mapped NAS drive)
4. Grant permissions when prompted

---

## Usage on Windows

### Run Tests
```powershell
cd Z:\
.\venv\Scripts\activate
python test_ai_router.py
```

### Run Demo
```powershell
python demo_agent.py
```

### Use Isaac Agent
```powershell
python -c "from isaac.ai import IsaacAgent; agent = IsaacAgent(); print(agent.chat('Hello'))"
```

---

## Cross-Platform Development Workflow

### Simultaneous Development

**Linux Side:**
```bash
cd ~/isaac-nas  # Symlink to NAS
source venv/bin/activate
python demo_agent.py
```

**Windows Side:**
```powershell
cd Z:\
.\venv\Scripts\activate
python demo_agent.py
```

### Important Notes

1. **Separate Virtual Environments**
   - Linux: Use `/home/birdman/Projects/Isaac/venv` (local)
   - Windows: Use `Z:\venv` (on NAS)
   - They must be separate because venv is platform-specific

2. **Git Repository**
   - DO NOT put `.git` on NAS (already excluded)
   - Keep git repos local on each machine
   - Use NAS only for source code sharing

3. **Testing Strategy**
   - Test on Linux: Linux-specific features
   - Test on Windows: Windows-specific features (PowerShell adapter)
   - Test both: AI routing, tools, cross-platform code

4. **Claude Code Sessions**
   - Linux Claude Code: Work on Linux issues
   - Windows Claude Code: Work on Windows issues
   - Both can debug the same codebase simultaneously
   - Changes are instantly visible on both sides

---

## Recommended Workflow

### Initial Setup (One Time)

**On Linux:**
```bash
cd /home/birdman/Projects/Isaac
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**On Windows:**
```powershell
cd Z:\
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Daily Development

**Option 1: Linux Primary**
1. Work on Linux with Claude Code
2. Make changes to `~/isaac-nas/`
3. Test on Windows when needed
4. Both machines see changes instantly

**Option 2: Windows Primary**
1. Work on Windows with Claude Code
2. Make changes to `Z:\`
3. Test on Linux when needed
4. Both machines see changes instantly

**Option 3: Simultaneous (Advanced)**
1. Linux Claude Code: Debug Linux-specific issues
2. Windows Claude Code: Debug Windows-specific issues
3. Both work on same files (be careful with conflicts!)
4. Coordinate via comments in code

---

## Troubleshooting

### Windows Cannot Access NAS
- Verify network: `ping 192.168.12.10`
- Try IP instead of hostname: `\\192.168.12.10\share\ISAAC`
- Check Windows Firewall settings
- Verify SMB is enabled: `Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol`

### Virtual Environment Issues
- Windows: Must use `.\venv\Scripts\activate`
- Linux: Must use `source venv/bin/activate`
- Never share venv between platforms

### File Permission Errors
- Normal on SMB shares
- Files may show as executable (don't worry)
- Git won't work properly on SMB (use local git)

### Import Errors
- Make sure venv is activated
- Check you're in correct directory
- Verify dependencies: `pip list`

---

## File Structure on NAS

```
Z:\ (or ~/isaac-nas on Linux)
├── isaac/                  # Main codebase
│   ├── ai/                # AI routing system
│   ├── tools/             # File operation tools
│   ├── commands/          # Command plugins
│   └── core/              # Core functionality
├── tests/                 # Unit tests
├── venv/                  # Windows virtual environment
├── requirements.txt
├── setup.py
├── README.md
├── WINDOWS_SETUP.md       # This file
└── CROSS_PLATFORM_DEV.md  # Coming soon
```

---

## Next Steps

1. ✅ Map network drive on Windows
2. ✅ Install Python on Windows
3. ✅ Create Windows venv on NAS
4. ✅ Install Claude Code for Windows
5. ✅ Test basic functionality
6. ✅ Start cross-platform development!

---

*Last Updated: November 8, 2025*
