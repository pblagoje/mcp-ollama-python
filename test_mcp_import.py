import sys
import os

# Clear PYTHONPATH
os.environ.pop('PYTHONPATH', None)

print("Python executable:", sys.executable)
print("\nFirst 10 sys.path entries:")
for i, p in enumerate(sys.path[:10], 1):
    print(f"{i}. {p}")

print("\n" + "="*60)
print("Testing mcp import...")
try:
    import mcp
    print("SUCCESS: mcp imported")
    print(f"mcp location: {mcp.__file__}")
except ImportError as e:
    print(f"FAILED: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("Testing module run simulation...")
# Simulate what happens when running -m ollama_mcp_python
try:
    # Add src to path like the .pth file does
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # Now try to import the main module
    from ollama_mcp_python import main
    print("SUCCESS: ollama_mcp_python.main imported")
except SystemExit as e:
    print(f"FAILED: Module called sys.exit({e.code})")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
