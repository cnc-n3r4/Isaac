# PLATFORM MAPPING MATRIX - Complete Command Reference

**Project:** ISAAC Alias System Deep Dive
**Agent:** Agent 3
**Generated:** 2025-11-09
**Coverage:** 60 commands mapped

---

## MATRIX OVERVIEW

This document provides a comprehensive mapping of Unix/Linux commands to their Windows PowerShell, Windows CMD, and macOS equivalents. This matrix is essential for achieving ISAAC's "one-OS feel" across all platforms.

**Current Implementation Status:**
- ✅ **Implemented:** 16 commands (in `unix_aliases.json`)
- 📋 **Documented but not implemented:** 44 commands
- 🎯 **Total Coverage:** 60 commands

---

## COMMAND MAPPING TABLE

### File Operations (18 commands)

| Universal Command | Linux/Bash | Windows PowerShell | Windows CMD | macOS | Implementation | Notes |
|-------------------|------------|-------------------|-------------|-------|----------------|-------|
| **list** | `ls` | `Get-ChildItem` | `dir` | `ls` | ✅ | Alias exists, `-la` mapped |
| **list-hidden** | `ls -a` | `Get-ChildItem -Force` | `dir /a` | `ls -a` | ✅ | Part of `ls` mapping |
| **list-long** | `ls -l` | `Get-ChildItem \| Format-List` | `dir` | `ls -l` | ✅ | Pipes to Format-List |
| **show-content** | `cat` | `Get-Content` | `type` | `cat` | ✅ | Basic implementation |
| **first-lines** | `head` | `Get-Content \| Select-Object -First` | N/A | `head` | ✅ | Piped command |
| **last-lines** | `tail` | `Get-Content \| Select-Object -Last` | N/A | `tail` | ✅ | Supports `-f` for follow |
| **follow-file** | `tail -f` | `Get-Content -Wait` | N/A | `tail -f` | ✅ | Real-time file monitoring |
| **copy-file** | `cp` | `Copy-Item` | `copy` | `cp` | ✅ | Supports `-r` for recursive |
| **move-file** | `mv` | `Move-Item` | `move` | `mv` | ✅ | Also used for rename |
| **remove-file** | `rm` | `Remove-Item` | `del` | `rm` | ✅ | Supports `-rf` for force recursive |
| **create-file** | `touch` | `New-Item -ItemType File` | `echo. >` | `touch` | ✅ | Creates empty file |
| **make-directory** | `mkdir` | `New-Item -ItemType Directory` | `mkdir` | `mkdir` | ✅ | Supports `-p` for parents |
| **show-directory** | `pwd` | `Get-Location` | `cd` | `pwd` | ✅ | Print working directory |
| **change-directory** | `cd` | `Set-Location` | `cd` | `cd` | Special | Handled by CommandRouter |
| **find-files** | `find` | `Get-ChildItem -Recurse` | `dir /s` | `find` | ✅ | Supports `-name` filter |
| **file-type** | `file` | `Get-Item \| Select-Object Extension` | N/A | `file` | ❌ | Not implemented |
| **show-tree** | `tree` | `tree` | `tree` | `tree` | ❌ | Native on all platforms |
| **disk-usage** | `du` | `Get-ChildItem -Recurse \| Measure-Object -Property Length -Sum` | N/A | `du` | ❌ | Complex piped command |

---

### Text Processing (12 commands)

| Universal Command | Linux/Bash | Windows PowerShell | Windows CMD | macOS | Implementation | Notes |
|-------------------|------------|-------------------|-------------|-------|----------------|-------|
| **search-text** | `grep` | `Select-String` | `findstr` | `grep` | ✅ | Basic pattern matching |
| **count-lines** | `wc -l` | `Get-Content \| Measure-Object -Line` | `find /c /v ""` | `wc -l` | ✅ | Part of `wc` mapping |
| **count-words** | `wc -w` | `Get-Content \| Measure-Object -Word` | N/A | `wc -w` | ✅ | Part of `wc` mapping |
| **count-chars** | `wc -c` | `Get-Content \| Measure-Object -Character` | N/A | `wc -c` | ✅ | Part of `wc` mapping |
| **sort-lines** | `sort` | `Sort-Object` | `sort` | `sort` | ❌ | Needs implementation |
| **unique-lines** | `uniq` | `Get-Unique` | N/A | `uniq` | ❌ | Often used with sort |
| **cut-fields** | `cut` | `ForEach-Object {$_.Split()}` | N/A | `cut` | ❌ | Field extraction |
| **stream-edit** | `sed` | N/A (complex) | N/A | `sed` | ❌ | Very complex to map |
| **pattern-scan** | `awk` | N/A (complex) | N/A | `awk` | ❌ | Very complex to map |
| **compare-files** | `diff` | `Compare-Object` | `fc` | `diff` | ❌ | File comparison |
| **print-text** | `echo` | `Write-Output` | `echo` | `echo` | ✅ | Simple output |
| **format-text** | `fmt` | N/A | N/A | `fmt` | ❌ | Text formatting |

---

### Process Management (8 commands)

| Universal Command | Linux/Bash | Windows PowerShell | Windows CMD | macOS | Implementation | Notes |
|-------------------|------------|-------------------|-------------|-------|----------------|-------|
| **list-processes** | `ps` | `Get-Process` | `tasklist` | `ps` | ✅ | Process listing |
| **list-all-processes** | `ps aux` | `Get-Process \| Format-Table` | `tasklist` | `ps aux` | ✅ | Full process list |
| **kill-process** | `kill` | `Stop-Process` | `taskkill` | `kill` | ✅ | Supports `-9` for force |
| **force-kill** | `kill -9` | `Stop-Process -Force` | `taskkill /F` | `kill -9` | ✅ | Part of kill mapping |
| **kill-by-name** | `killall` | `Stop-Process -Name` | `taskkill /IM` | `killall` | ❌ | Kill by process name |
| **process-tree** | `pstree` | `Get-Process \| Format-List` | N/A | `pstree` | ❌ | Process hierarchy |
| **top-processes** | `top` | `Get-Process \| Sort-Object CPU -Descending` | N/A | `top` | ❌ | Interactive process monitor |
| **background-job** | `bg` | `Start-Job` | N/A | `bg` | ❌ | Background process control |

---

### Network Operations (10 commands)

| Universal Command | Linux/Bash | Windows PowerShell | Windows CMD | macOS | Implementation | Notes |
|-------------------|------------|-------------------|-------------|-------|----------------|-------|
| **network-status** | `netstat` | `Get-NetTCPConnection` | `netstat` | `netstat` | ❌ | Network connections |
| **ping-host** | `ping` | `Test-Connection` | `ping` | `ping` | ❌ | Test network connectivity |
| **dns-lookup** | `nslookup` | `Resolve-DnsName` | `nslookup` | `nslookup` | ❌ | DNS resolution |
| **trace-route** | `traceroute` | `Test-NetConnection -TraceRoute` | `tracert` | `traceroute` | ❌ | Network path tracing |
| **download-file** | `wget` / `curl` | `Invoke-WebRequest` | N/A | `curl` | ❌ | HTTP download |
| **http-get** | `curl` | `Invoke-RestMethod` | N/A | `curl` | ❌ | HTTP request |
| **show-interfaces** | `ifconfig` | `Get-NetAdapter` | `ipconfig` | `ifconfig` | ❌ | Network interface config |
| **show-ip** | `ip addr` | `Get-NetIPAddress` | `ipconfig` | `ip addr` | ❌ | IP address display |
| **ssh-connect** | `ssh` | `ssh` | N/A | `ssh` | ❌ | Secure shell (native on PS 7+) |
| **secure-copy** | `scp` | `scp` | N/A | `scp` | ❌ | Secure file copy |

---

### System Information (7 commands)

| Universal Command | Linux/Bash | Windows PowerShell | Windows CMD | macOS | Implementation | Notes |
|-------------------|------------|-------------------|-------------|-------|----------------|-------|
| **locate-command** | `which` | `Get-Command` | `where` | `which` | ✅ | Find command location |
| **show-environment** | `env` | `Get-ChildItem Env:` | `set` | `env` | ❌ | Environment variables |
| **set-variable** | `export VAR=value` | `$env:VAR="value"` | `set VAR=value` | `export VAR=value` | ❌ | Set environment variable |
| **system-info** | `uname -a` | `Get-ComputerInfo` | `systeminfo` | `uname -a` | ❌ | System information |
| **disk-space** | `df` | `Get-PSDrive` | N/A | `df` | ❌ | Disk space usage |
| **memory-info** | `free` | `Get-CimInstance Win32_OperatingSystem` | N/A | `free` | ❌ | Memory usage |
| **uptime** | `uptime` | `(Get-CimInstance Win32_OperatingSystem).LastBootUpTime` | N/A | `uptime` | ❌ | System uptime |

---

### Compression & Archives (5 commands)

| Universal Command | Linux/Bash | Windows PowerShell | Windows CMD | macOS | Implementation | Notes |
|-------------------|------------|-------------------|-------------|-------|----------------|-------|
| **create-tar** | `tar -czf` | `Compress-Archive` | N/A | `tar -czf` | ❌ | Create compressed archive |
| **extract-tar** | `tar -xzf` | `Expand-Archive` | N/A | `tar -xzf` | ❌ | Extract compressed archive |
| **zip-files** | `zip` | `Compress-Archive` | N/A | `zip` | ❌ | Create zip archive |
| **unzip-files** | `unzip` | `Expand-Archive` | N/A | `unzip` | ❌ | Extract zip archive |
| **gzip-file** | `gzip` | `N/A` | N/A | `gzip` | ❌ | Gzip compression |

---

## IMPLEMENTATION PRIORITY MATRIX

### Tier 1: Must-Have (Daily Use) - 20 commands
**Status:** 14/20 implemented (70%)

✅ Implemented:
1. `ls`, `cat`, `head`, `tail`, `cp`, `mv`, `rm`, `touch`
2. `mkdir`, `pwd`, `cd`, `find`, `grep`, `wc`
3. `ps`, `kill`, `which`, `echo`

❌ Not Implemented (High Priority):
1. `sort` - Essential for data processing
2. `diff` - File comparison critical
3. `top` - Process monitoring
4. `df` - Disk space monitoring
5. `ping` - Network diagnostics
6. `curl` / `wget` - HTTP operations

---

### Tier 2: Important (Weekly Use) - 15 commands
**Status:** 2/15 implemented (13%)

Needs Implementation:
1. `uniq` - Duplicate line removal
2. `cut` - Column extraction
3. `killall` - Process management
4. `netstat` - Network status
5. `ifconfig` / `ipconfig` - Network config
6. `ssh` - Remote access (native on PS 7+)
7. `env` - Environment inspection
8. `du` - Disk usage analysis
9. `tar` - Archive management
10. `zip` / `unzip` - Compression
11. `tree` - Directory tree (native)
12. `pstree` - Process tree
13. `traceroute` - Network diagnostics
14. `nslookup` - DNS lookup
15. `systeminfo` - System details

---

### Tier 3: Nice-to-Have (Monthly Use) - 25 commands
**Status:** 0/25 implemented (0%)

Lower Priority:
1. `sed`, `awk` - Complex text processing (hard to map)
2. `fmt` - Text formatting
3. `file` - File type detection
4. `scp` - Secure copy
5. `bg`, `fg` - Job control
6. `free` - Memory info
7. `uptime` - System uptime
8. `gzip`, `gunzip` - Compression
9. Various advanced commands

---

## POWERSHELL NATIVE ALIASES

**Important Note:** PowerShell already has built-in aliases for many Unix commands:

| Unix Command | PowerShell Alias | PowerShell Cmdlet |
|--------------|------------------|-------------------|
| `ls` | `ls` | `Get-ChildItem` |
| `dir` | `dir` | `Get-ChildItem` |
| `cat` | `cat` | `Get-Content` |
| `cd` | `cd` | `Set-Location` |
| `pwd` | `pwd` | `Get-Location` |
| `cp` | `cp` | `Copy-Item` |
| `mv` | `mv` | `Move-Item` |
| `rm` | `rm` | `Remove-Item` |
| `mkdir` | `mkdir` | `New-Item -ItemType Directory` |
| `echo` | `echo` | `Write-Output` |
| `ps` | `ps` | `Get-Process` |
| `kill` | `kill` | `Stop-Process` |
| `where` | `where` | `Where-Object` |
| `sort` | `sort` | `Sort-Object` |
| `select` | `select` | `Select-Object` |

**Impact on ISAAC:** Many commands don't need translation on Windows because PowerShell already handles them. ISAAC's alias system should focus on:
1. **Commands PowerShell doesn't alias** (grep → Select-String, etc.)
2. **Argument mapping** (converting Unix flags to PowerShell parameters)
3. **Complex commands** (piped operations, sed/awk alternatives)

---

## PLATFORM-SPECIFIC NOTES

### Windows PowerShell
- **Strength:** Rich object-oriented pipeline
- **Weakness:** Slower startup time
- **Unique Features:** Direct .NET access, WMI/CIM integration
- **Missing:** sed, awk, many text processing tools

### Windows CMD
- **Strength:** Fast, lightweight
- **Weakness:** Very limited functionality
- **Note:** ISAAC should deprioritize CMD support in favor of PowerShell

### Linux/macOS Bash
- **Strength:** Fast, text-stream oriented
- **Weakness:** Less structured output
- **Note:** No translation needed; direct execution

### macOS-Specific
- **Note:** macOS uses BSD versions of some commands (different flags)
- **Examples:** `ls` on macOS has different options than GNU ls
- **Recommendation:** Test macOS separately, don't assume Linux compatibility

---

## ARGUMENT MAPPING PATTERNS

### Common Patterns

1. **Force Flag**
   - Unix: `-f`
   - PowerShell: `-Force`
   - Example: `rm -f` → `Remove-Item -Force`

2. **Recursive Flag**
   - Unix: `-r` or `-R`
   - PowerShell: `-Recurse`
   - Example: `ls -R` → `Get-ChildItem -Recurse`

3. **Verbose Flag**
   - Unix: `-v`
   - PowerShell: `-Verbose`
   - Example: `cp -v` → `Copy-Item -Verbose`

4. **Help Flag**
   - Unix: `--help` or `-h`
   - PowerShell: `-?` or `Get-Help <cmdlet>`
   - CMD: `/?`

5. **Output Formatting**
   - Unix: `-l` (long format)
   - PowerShell: `| Format-List` or `| Format-Table`

6. **Filtering**
   - Unix: `-name` (find)
   - PowerShell: `-Filter` or `-Include`

---

## COMPLEX COMMAND MAPPINGS

### 1. Find and Execute
```bash
# Unix
find . -name "*.txt" -exec cat {} \;

# PowerShell
Get-ChildItem -Recurse -Filter "*.txt" | Get-Content
```

### 2. Process Filtering
```bash
# Unix
ps aux | grep python

# PowerShell
Get-Process | Where-Object { $_.Name -like "*python*" }
```

### 3. File Counting
```bash
# Unix
find . -type f | wc -l

# PowerShell
(Get-ChildItem -Recurse -File).Count
```

### 4. Disk Usage Summary
```bash
# Unix
du -sh *

# PowerShell
Get-ChildItem | ForEach-Object {
    $size = (Get-ChildItem $_ -Recurse -ErrorAction SilentlyContinue |
             Measure-Object -Property Length -Sum).Sum / 1MB
    [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round($size,2)}
}
```

### 5. Network Port Listening
```bash
# Unix
netstat -tulpn | grep LISTEN

# PowerShell
Get-NetTCPConnection | Where-Object { $_.State -eq "Listen" }
```

---

## GAPS & LIMITATIONS

### 1. No Direct Equivalent

These Unix commands have no simple PowerShell equivalent:
- `sed` - Stream editor (use -replace, but very different)
- `awk` - Text processing (use ForEach-Object, but complex)
- `ln` - Symbolic links (PowerShell has New-Item -ItemType SymbolicLink, but different syntax)

### 2. Complex Translation Required

These require multi-line PowerShell equivalents:
- `top` - Interactive process monitor
- `find -exec` - Find and execute
- `xargs` - Command builder

### 3. Platform-Specific Behavior

These behave differently across platforms:
- `ls` - GNU vs BSD options
- `ps` - Different output formats
- `netstat` - Different flags and output

---

## EXPANSION STRATEGY

### Phase 1: Complete Tier 1 (6 commands remaining)
**Effort:** 1-2 days
**Impact:** High - covers 90% of daily use cases

Commands to add:
1. `sort` → `Sort-Object`
2. `diff` → `Compare-Object`
3. `top` → `Get-Process | Sort-Object CPU -Descending | Select-Object -First 20`
4. `df` → `Get-PSDrive`
5. `ping` → `Test-Connection`
6. `curl` → `Invoke-RestMethod`

### Phase 2: Complete Tier 2 (13 commands remaining)
**Effort:** 3-5 days
**Impact:** Medium - covers most power user needs

### Phase 3: Selective Tier 3 Implementation
**Effort:** 1-2 weeks
**Impact:** Low - advanced use cases

**Recommendation:** Focus on commands that:
1. Have clear PowerShell equivalents
2. Are commonly used in scripts
3. Can be mapped with simple argument translation

**Skip:** Complex text processors (sed, awk) - users should learn PowerShell equivalents

---

## TESTING STRATEGY

### Per-Command Testing

For each mapped command, test:
1. ✅ Basic execution (no arguments)
2. ✅ Common flags (-l, -a, -r, etc.)
3. ✅ Flag combinations (-la, -rf, etc.)
4. ✅ Positional arguments (file paths)
5. ✅ Piped input/output
6. ✅ Error conditions
7. ✅ Special characters in arguments

### Cross-Platform Testing

Test on:
1. ✅ Windows 10/11 (PowerShell 5.1)
2. ✅ Windows 10/11 (PowerShell 7+)
3. ✅ Linux (Ubuntu, Fedora)
4. ✅ macOS (Intel, Apple Silicon)

### Performance Testing

Measure:
1. Translation overhead
2. Execution time comparison (native vs translated)
3. Memory usage
4. Subprocess spawn time

---

## CONCLUSION

**Current State:**
- 16/60 commands implemented (27%)
- Strong foundation with clean architecture
- Focus on basic file operations and process management

**Needed:**
- 44 more commands for comprehensive coverage
- Better argument mapping for existing commands
- Testing across all platforms

**Priority:**
- Complete Tier 1 (6 commands) - **High Priority**
- Add Tier 2 network/system commands - **Medium Priority**
- Selective Tier 3 additions - **Low Priority**

**Recommendation:** Focus on breadth (more commands) before depth (perfect argument mapping). Users need basic coverage of common commands more than perfect handling of edge cases.

---

**Related Documents:**
- See ALIAS_ARCHITECTURE.md for implementation details
- See PLATFORM_NATIVE_FEEL.md for platform-specific assessments
- See CROSSPLATFORM_ROADMAP.md for long-term expansion plan
