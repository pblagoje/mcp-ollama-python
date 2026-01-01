#!/usr/bin/env python
"""
Test runner for mcp-ollama-python

Usage:
    python run_tests.py              # Run all tests
    python run_tests.py -v           # Run with verbose output
    python run_tests.py -k "test_"   # Run specific tests
    python run_tests.py --cov        # Run with coverage
"""

import sys
import os
import subprocess
from pathlib import Path


def main():
    """Run the test suite"""
    # Get the project root directory (parent of scripts folder)
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    src_dir = project_root / "src"
    
    # Add src to PYTHONPATH for imports
    env = os.environ.copy()
    python_path = str(src_dir)
    if "PYTHONPATH" in env:
        python_path = f"{python_path}{os.pathsep}{env['PYTHONPATH']}"
    env["PYTHONPATH"] = python_path
    
    # Build pytest command
    pytest_args = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "-x",  # Stop on first failure (remove for full run)
    ]
    
    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        # Remove -x if user wants full run
        if "--full" in sys.argv:
            pytest_args.remove("-x")
            sys.argv.remove("--full")
        pytest_args.extend(sys.argv[1:])
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"Using pytest version: {pytest.__version__}")
    except ImportError:
        print("pytest not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
    
    # Check if pytest-asyncio is installed (needed for async tests)
    try:
        import pytest_asyncio
        print(f"Using pytest-asyncio version: {pytest_asyncio.__version__}")
    except ImportError:
        print("pytest-asyncio not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest-asyncio"])
    
    print(f"\n{'='*60}")
    print("Running mcp-ollama-python tests")
    print(f"{'='*60}")
    print(f"Tests directory: {tests_dir}")
    print(f"Source directory: {src_dir}")
    print(f"PYTHONPATH: {env['PYTHONPATH']}")
    print(f"{'='*60}\n")
    
    # Run pytest
    result = subprocess.run(pytest_args, env=env, cwd=str(project_root))
    
    print(f"\n{'='*60}")
    if result.returncode == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed with exit code: {result.returncode}")
    print(f"{'='*60}")
    
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
