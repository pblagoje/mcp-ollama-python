#!/usr/bin/env python
"""Test script to diagnose mcp import issue"""
import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"\nPython path (first 10 entries):")
for i, path in enumerate(sys.path[:10], 1):
    print(f"  {i}. {path}")

print("\n" + "="*60)
print("Testing direct mcp import...")
try:
    import mcp
    print(f"✓ mcp imported successfully")
    print(f"  Location: {mcp.__file__}")
    print(f"  Version: {getattr(mcp, '__version__', 'unknown')}")
except ImportError as e:
    print(f"✗ Failed to import mcp: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("Testing ollama_mcp_python module import...")
try:
    import ollama_mcp_python
    print(f"✓ ollama_mcp_python imported successfully")
    print(f"  Location: {ollama_mcp_python.__file__}")
except ImportError as e:
    print(f"✗ Failed to import ollama_mcp_python: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("Testing ollama_mcp_python.main import...")
try:
    from ollama_mcp_python import main
    print(f"✓ ollama_mcp_python.main imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ollama_mcp_python.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*60)
print("All imports successful!")
