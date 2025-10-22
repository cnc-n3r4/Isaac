"""Debug config loading - check what's actually in memory"""

import json
from pathlib import Path

# Check what's on disk
home = Path.home()
isaac_dir = home / '.isaac'
config_file = isaac_dir / 'config.json'

print("=" * 60)
print("CONFIG FILE DEBUG")
print("=" * 60)
print(f"\nLooking for config at: {config_file}")
print(f"File exists: {config_file.exists()}")

if config_file.exists():
    print("\n" + "=" * 60)
    print("RAW FILE CONTENT:")
    print("=" * 60)
    with open(config_file, 'r') as f:
        content = f.read()
        print(content)
    
    print("\n" + "=" * 60)
    print("PARSING JSON...")
    print("=" * 60)
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ JSON PARSE ERROR: {e}")
        print(f"\nError at line {e.lineno}, column {e.colno}")
        print(f"Message: {e.msg}")
        
        # Show the problematic line
        lines = content.split('\n')
        if e.lineno <= len(lines):
            print(f"\nProblematic line {e.lineno}:")
            print(f"  {lines[e.lineno - 1]}")
            if e.colno > 0:
                print(f"  {' ' * (e.colno - 1)}^ HERE")
        
        print("\n" + "=" * 60)
        print("COMMON JSON ERRORS:")
        print("=" * 60)
        print("1. Missing comma after a value")
        print("2. Trailing comma before closing }")
        print("3. Keys not in double quotes")
        print("4. Missing closing bracket/brace")
        print("\nI'll create a corrected config.json.FIXED for you...")
        
        # Create a fixed version
        import sys
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("PARSED JSON:")
    print("=" * 60)
    with open(config_file, 'r') as f:
        data = json.load(f)
        print(json.dumps(data, indent=2))
    
    print("\n" + "=" * 60)
    print("KEY CHECKS:")
    print("=" * 60)
    
    # Check xai structure
    if 'xai' in data:
        print("✓ 'xai' key exists")
        xai = data['xai']
        
        if 'chat' in xai:
            print("  ✓ 'xai.chat' exists")
            if 'api_key' in xai['chat']:
                key = xai['chat']['api_key']
                print(f"    ✓ 'xai.chat.api_key' = '{key[:10]}...'")
            else:
                print("    ✗ 'xai.chat.api_key' MISSING")
        else:
            print("  ✗ 'xai.chat' MISSING")
        
        if 'collections' in xai:
            print("  ✓ 'xai.collections' exists")
            if 'api_key' in xai['collections']:
                key = xai['collections']['api_key']
                print(f"    ✓ 'xai.collections.api_key' = '{key[:10]}...'")
            else:
                print("    ✗ 'xai.collections.api_key' MISSING")
        else:
            print("  ✗ 'xai.collections' MISSING")
    else:
        print("✗ 'xai' key MISSING")
    
    # Check flat structure (old style)
    if 'xai_api_key' in data:
        key = data['xai_api_key']
        print(f"\n⚠ Found flat 'xai_api_key' = '{key[:10]}...'")
        print("  (This is old structure - should be nested)")

else:
    print("\n⚠ Config file does not exist!")
    print("Create it at the path above with proper structure.")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("1. If file exists but keys are wrong, fix the structure")
print("2. If file doesn't exist, create it")
print("3. Run: isaac")
print("4. Try: /ask hello")
print("5. Try: /mine ls")
