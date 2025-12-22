#!/usr/bin/env python
"""Detailed test to find the exact import issue"""
import sys
import os

print("="*60)
print("STEP 1: Direct mcp import test")
print("="*60)
try:
    import mcp
    print("✓ Direct mcp import successful")
    print(f"  mcp.__file__ = {mcp.__file__}")
except Exception as e:
    print(f"✗ Direct mcp import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("STEP 2: Import ollama_mcp_python package")
print("="*60)
try:
    import ollama_mcp_python
    print("✓ ollama_mcp_python package imported")
except Exception as e:
    print(f"✗ ollama_mcp_python import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("STEP 3: Check sys.modules for mcp")
print("="*60)
if 'mcp' in sys.modules:
    print(f"✓ mcp is in sys.modules")
    print(f"  mcp module: {sys.modules['mcp']}")
else:
    print("✗ mcp is NOT in sys.modules")

print("\n" + "="*60)
print("STEP 4: Try importing from ollama_mcp_python.main")
print("="*60)
print("This will trigger the import in main.py...")

# Clear mcp from sys.modules to simulate fresh import
if 'mcp' in sys.modules:
    print("Clearing mcp from sys.modules to simulate fresh import...")
    del sys.modules['mcp']

try:
    from ollama_mcp_python import main
    print("✓ ollama_mcp_python.main imported successfully!")
except SystemExit as e:
    print(f"✗ SystemExit caught: {e}")
    print("The main.py module called sys.exit() due to import failure")
except Exception as e:
    print(f"✗ Import failed with exception: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("STEP 5: Check if mcp is back in sys.modules")
print("="*60)
if 'mcp' in sys.modules:
    print(f"✓ mcp is in sys.modules: {sys.modules['mcp']}")
else:
    print("✗ mcp is NOT in sys.modules")
