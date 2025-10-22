"""Show raw config content with line numbers"""

from pathlib import Path

home = Path.home()
config_file = home / '.isaac' / 'config.json'

print("=" * 60)
print("RAW CONFIG WITH LINE NUMBERS:")
print("=" * 60)

if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, start=1):
        # Show line number and content (with visible whitespace)
        print(f"{i:3d} | {repr(line)}")
    
    print("\n" + "=" * 60)
    print("ACTUAL CONTENT:")
    print("=" * 60)
    with open(config_file, 'r', encoding='utf-8') as f:
        print(f.read())

else:
    print("Config file doesn't exist!")
