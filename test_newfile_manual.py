#!/usr/bin/env python3
"""
Simple test for /newfile command
"""

import json
import subprocess
import sys
from pathlib import Path

def test_newfile():
    """Test the newfile command"""
    print("Testing /newfile command...")

    # Test data
    test_payload = {
        "args": {
            "file": "test_file.txt",
            "content": "Hello, this is a test file!"
        },
        "session": {}
    }

    # Run the command
    try:
        result = subprocess.run(
            [sys.executable, "isaac/commands/newfile/run.py"],
            input=json.dumps(test_payload),
            text=True,
            capture_output=True
        )

        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")

        # Parse the result
        if result.stdout:
            response = json.loads(result.stdout)
            print(f"Response: {json.dumps(response, indent=2)}")

            if response.get("ok"):
                print("✅ Command executed successfully")
                # Check if file was created
                test_file = Path("test_file.txt")
                if test_file.exists():
                    print(f"✅ File created: {test_file}")
                    content = test_file.read_text()
                    print(f"Content: {content}")
                    test_file.unlink()  # Clean up
                else:
                    print("❌ File was not created")
            else:
                print("❌ Command failed")
        else:
            print("❌ No output received")

    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_newfile()