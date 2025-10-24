# Isaac Key Management - Access Control Guide

## Overview

Isaac uses a sophisticated key-based access control system to manage who can use the system and what they can do. Keys are like passwords that grant specific permissions. This system ensures that only authorized users and automated systems can access Isaac's features.

## Why Keys Matter

Keys provide:
- **Security**: Control who can access Isaac
- **Granular Permissions**: Different access levels for different users
- **Audit Trail**: Track who did what
- **Automation**: Allow scripts and bots to use Isaac safely
- **Emergency Access**: Master key override for lost access

## Quick Start for Beginners

### Step 1: Check Current Keys
```bash
# Start Isaac
isaac /start

# Check if you have any keys
isaac /config --keys list

# If no keys exist, you'll need to create your first one
```

### Step 2: Create Your First Key
```bash
# Create a personal user key
isaac /config --keys create user mykey

# Save the key that gets displayed - you'll need it!
# Example output: Created user key 'mykey': abc123def456
```

### Step 3: Use Your Key
```bash
# Use the key with commands
isaac --key abc123def456 /status

# Or set it as default
export ISAAC_KEY=abc123def456
isaac /status
```

## Understanding Key Types

### User Key (Most Common)
```bash
# Create a user key for yourself
isaac /config --keys create user mypersonal

# Permissions: Full access to all commands
# Use: Daily Isaac usage, development, administration
```

### Daemon Key (For Automation)
```bash
# Create for background services
isaac /config --keys create daemon webhook

# Permissions: Background processing, webhooks, scheduled tasks
# Use: Web servers, cron jobs, automated systems
```

### Read-Only Key (Limited Access)
```bash
# Create for limited access
isaac /config --keys create readonly guest

# Permissions: View status, read configs, no execution
# Use: Monitoring, status checks, read-only access
```

### One-Shot Key (Single Use)
```bash
# Create for one-time use
isaac /config --keys create oneshot temp

# Permissions: Single command execution
# Use: Temporary access, testing, emergency fixes
```

### Persona Keys (For AI Agents)
```bash
# Create for specific AI personas
isaac /config --keys create persona sarah
isaac /config --keys create persona daniel

# Permissions: Persona-specific access
# Use: Different AI agents with different capabilities
```

## Basic Key Management

### Creating Keys
```bash
# Create with auto-generated name
isaac /config --keys create user

# Create with custom name
isaac /config --keys create user john

# Create for specific persona
isaac /config --keys create persona assistant
```

### Listing Keys
```bash
# Show all your keys
isaac /config --keys list

# Example output:
# Name: mykey
# Type: user
# Created: 2025-10-24 10:30:00
# Permissions: execute, configure, manage
```

### Testing Keys
```bash
# Test if a key is valid
isaac /config --keys test abc123def456

# Example output:
# ✓ Key authenticated
# Type: user
# Permissions: execute, configure, manage
```

### Deleting Keys
```bash
# Remove a key (be careful!)
isaac /config --keys delete mykey

# Confirm deletion
isaac /config --keys list  # Verify it's gone
```

## Advanced Key Features

### Master Key System (Emergency Override)

#### When You Need Master Keys
- Lost all your regular keys
- System locked out
- Emergency access required
- Testing key recovery

#### Setting Up Master Key
```bash
# Create a master key file
isaac /config --keys master set myemergencykey

# This creates a secure master key file
# Keep this key in a safe place!
```

#### Using Master Key
```bash
# Override with master key
isaac --master-key myemergencykey /config --keys create user recovery

# Or use environment variable
export ISAAC_MASTER_KEY=myemergencykey
isaac /config --keys create user recovery
```

#### Master Key Status
```bash
# Check master key status
isaac /config --keys master status

# Remove master key
isaac /config --keys master remove
```

### Key Expiration (Advanced)
```bash
# Keys can be set to expire (not implemented in basic version)
# Future feature for temporary access
```

## Using Keys in Practice

### Command Line Usage
```bash
# Direct key specification
isaac --key abc123def456 /status

# Environment variable (recommended)
export ISAAC_KEY=abc123def456
isaac /status

# Master key override
isaac --master-key masterkey /config --keys create user newkey
```

### Configuration Integration
```bash
# Keys work with all Isaac features
isaac --key mykey /mine --dig "search term"
isaac --key mykey /config console
isaac --key mykey workspace create newproject
```

### Automation Scripts
```bash
#!/bin/bash
# Example automation script
export ISAAC_KEY=daemon123
isaac /mine --cast newfile.txt
isaac /status
```

## Key Security Best Practices

### Storage
- **Never hardcode keys** in scripts or config files
- **Use environment variables** for automation
- **Store master keys offline** (USB drive, password manager)
- **Rotate keys regularly** for important systems

### Access Control
- **Use read-only keys** for monitoring systems
- **One-shot keys** for temporary access
- **Persona keys** for different AI agents
- **Separate keys** for different environments (dev/staging/prod)

### Monitoring
```bash
# Check key usage
isaac /config --keys list

# Monitor for suspicious activity
isaac /status  # Shows recent activity
```

## Troubleshooting Key Issues

### "Key not found" Error
```bash
# Check if key exists
isaac /config --keys list

# Test the key
isaac /config --keys test yourkey

# Create new key if needed
isaac /config --keys create user replacement
```

### "Insufficient permissions" Error
```bash
# Check key type and permissions
isaac /config --keys test yourkey

# You might need a different key type
isaac /config --keys create user fullaccess
```

### Lost All Keys (Emergency Recovery)
```bash
# Use master key if you have one
isaac --master-key yourmasterkey /config --keys create user recovery

# Or set environment variable
export ISAAC_MASTER_KEY=yourmasterkey
isaac /config --keys create user recovery
```

### Master Key Not Working
```bash
# Check master key status
isaac /config --keys master status

# Recreate master key file
isaac /config --keys master set newmasterkey
```

## Key Management for Teams

### Team Setup
```bash
# Admin creates team keys
isaac /config --keys create user alice
isaac /config --keys create user bob
isaac /config --keys create readonly monitor

# Share keys securely (not by email!)
# Use encrypted chat, password manager, etc.
```

### Role-Based Access
- **Admin**: Full user keys
- **Developer**: User keys with development permissions
- **Ops**: Daemon keys for automation
- **Monitor**: Read-only keys for dashboards

### Key Rotation
```bash
# Regular key rotation for security
# Create new keys
isaac /config --keys create user alice-new

# Test new keys work
isaac --key alice-new-key /status

# Delete old keys
isaac /config --keys delete alice-old

# Update team with new keys
```

## Integration with Other Systems

### CI/CD Pipelines
```yaml
# Example GitHub Actions
- name: Use Isaac
  env:
    ISAAC_KEY: ${{ secrets.ISAAC_DAEMON_KEY }}
  run: |
    isaac /mine --cast build.log
    isaac /status
```

### Web Applications
```python
# Example web app integration
import os
import subprocess

def run_isaac_command(command):
    key = os.getenv('ISAAC_KEY')
    if not key:
        raise ValueError("ISAAC_KEY environment variable not set")

    full_command = f'isaac --key {key} {command}'
    result = subprocess.run(full_command, shell=True, capture_output=True, text=True)
    return result.stdout
```

### Monitoring Systems
```bash
# Nagios/Icinga check
#!/bin/bash
OUTPUT=$(isaac --key readonly123 /status)
if [ $? -eq 0 ]; then
    echo "OK - Isaac is running"
    exit 0
else
    echo "CRITICAL - Isaac check failed"
    exit 2
fi
```

## Key Types Reference

| Key Type | Permissions | Use Case |
|----------|-------------|----------|
| user | execute, configure, manage | Full Isaac access |
| daemon | background, webhooks, automation | Server processes |
| readonly | status, read configs | Monitoring, dashboards |
| oneshot | single command | Temporary access |
| persona | persona-specific | AI agent access |
| master | emergency override | Lost key recovery |

## Getting Started Checklist

- [ ] Start Isaac: `isaac /start`
- [ ] Check existing keys: `isaac /config --keys list`
- [ ] Create your first key: `isaac /config --keys create user mykey`
- [ ] Save the key securely (password manager recommended)
- [ ] Test the key: `isaac --key YOURKEY /status`
- [ ] Set environment variable: `export ISAAC_KEY=YOURKEY`
- [ ] Create master key: `isaac /config --keys master set masterkey`
- [ ] Store master key offline and securely

## Security Reminders

- **Keys are like passwords** - treat them with the same care
- **Use different keys** for different purposes
- **Rotate keys regularly** for important systems
- **Monitor key usage** and watch for suspicious activity
- **Have a recovery plan** with master keys
- **Never share keys** in plain text or email

Keys are the foundation of Isaac's security model. Take the time to set them up properly, and you'll have a secure, controllable system that grows with your needs!</content>
<parameter name="filePath">c:\Projects\Isaac-1\instructions\key_management_guide.md