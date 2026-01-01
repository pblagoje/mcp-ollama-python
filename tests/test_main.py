"""Tests for main.py - Main entry point for Ollama MCP Server
python -m pytest tests/ -v
"""

import sys
import os
import pytest

# Package is installed, import from mcp_ollama_python


class TestMainModuleStructure:
    """Tests for main module structure and imports"""

    def test_main_module_imports(self):
        """Test that main module can be imported and has required components"""
        try:
            from mcp_ollama_python import main
            # Check main function exists
            assert hasattr(main, 'main')
            assert callable(main.main)
            
            # Check run function exists
            assert hasattr(main, 'run')
            assert callable(main.run)
        except ImportError as e:
            if 'mcp' in str(e).lower():
                pytest.skip(f"MCP package not available: {e}")
            raise

    def test_main_is_async_function(self):
        """Test that main function is an async function"""
        try:
            from mcp_ollama_python import main
            import asyncio
            assert asyncio.iscoroutinefunction(main.main)
        except ImportError as e:
            if 'mcp' in str(e).lower():
                pytest.skip(f"MCP package not available: {e}")
            raise

    def test_run_is_sync_function(self):
        """Test that run function is a regular sync function"""
        try:
            from mcp_ollama_python import main
            import asyncio
            # run() should be a sync function that calls asyncio.run()
            assert not asyncio.iscoroutinefunction(main.run)
        except ImportError as e:
            if 'mcp' in str(e).lower():
                pytest.skip(f"MCP package not available: {e}")
            raise


class TestMainModuleDependencies:
    """Tests for main module dependencies"""

    def test_ollama_client_imported(self):
        """Test OllamaClient is imported in main"""
        try:
            from mcp_ollama_python import main
            # The import happens at module level
            assert 'OllamaClient' in dir(main) or hasattr(main, 'OllamaClient')
        except ImportError as e:
            if 'mcp' in str(e).lower():
                pytest.skip(f"MCP package not available: {e}")
            raise

    def test_server_imported(self):
        """Test OllamaMCPServer is imported in main"""
        try:
            from mcp_ollama_python import main
            assert 'OllamaMCPServer' in dir(main) or hasattr(main, 'OllamaMCPServer')
        except ImportError as e:
            if 'mcp' in str(e).lower():
                pytest.skip(f"MCP package not available: {e}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
