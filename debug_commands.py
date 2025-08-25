#!/usr/bin/env python3
"""Debug script to check command registration"""
import sys
import traceback

# Test if imports work
try:
    from image_gen import ImageGenerator
    print("✓ ImageGenerator imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ImageGenerator: {e}")
    print("  This would prevent the imagine command from registering!")

# Test if PIL is available
try:
    from PIL import Image
    print("✓ PIL (Pillow) is installed")
except ImportError:
    print("✗ PIL (Pillow) is NOT installed - this breaks image_gen.py import")
    print("  Run: pip install Pillow")

# Try to parse server_setup.py and count commands
try:
    with open('server_setup.py', 'r') as f:
        content = f.read()
        
    import re
    commands = re.findall(r'@bot\.tree\.command\(name="([^"]+)"', content)
    print(f"\n Found {len(commands)} commands defined:")
    for cmd in commands:
        print(f"  - /{cmd}")
        
    if "imagine" in commands:
        print("\n✓ /imagine command is defined in code")
    else:
        print("\n✗ /imagine command NOT found in code!")
        
except Exception as e:
    print(f"Error checking commands: {e}")
    traceback.print_exc()