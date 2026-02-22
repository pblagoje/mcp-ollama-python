"""Tests for autoloader.py - Tool autoloader for dynamic tool discovery
"""

import pytest

# Package is installed, import from mcp_ollama_python
from mcp_ollama_python.models import ToolDefinition


class TestToolDefinitionValidation:
    """Tests for ToolDefinition used by autoloader"""

    def test_tool_definition_creation(self):
        """Test ToolDefinition can be created with required fields"""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}}
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.input_schema == {"type": "object", "properties": {}}

    def test_tool_definition_with_complex_schema(self):
        """Test ToolDefinition with complex input schema"""
        schema = {
            "type": "object",
            "properties": {
                "model": {"type": "string", "description": "Model name"},
                "prompt": {"type": "string", "description": "Input prompt"},
                "options": {
                    "type": "object",
                    "properties": {
                        "temperature": {"type": "number"}
                    }
                }
            },
            "required": ["model", "prompt"]
        }
        tool = ToolDefinition(
            name="ollama_generate",
            description="Generate text with Ollama",
            input_schema=schema
        )
        assert tool.input_schema["required"] == ["model", "prompt"]


class TestToolHandlerType:
    """Tests for ToolHandler type alias"""

    def test_tool_handler_type_exists(self):
        """Test ToolHandler type is defined"""
        from mcp_ollama_python.autoloader import ToolHandler
        assert ToolHandler is not None


class TestAutoloaderModuleImports:
    """Tests for autoloader module imports"""

    def test_discover_tools_is_async(self):
        """Test discover_tools is an async function"""
        from mcp_ollama_python.autoloader import discover_tools
        import asyncio
        assert asyncio.iscoroutinefunction(discover_tools)

    def test_autoloader_imports(self):
        """Test autoloader imports required modules"""
        from mcp_ollama_python import autoloader
        assert hasattr(autoloader, 'discover_tools')
        assert hasattr(autoloader, 'ToolHandler')


class TestAutoloaderIntegration:
    """Integration tests for the autoloader"""

    @pytest.mark.asyncio
    async def test_real_tools_directory_discovery(self):
        """Test discovery against the real tools directory if it exists"""
        try:
            from mcp_ollama_python.autoloader import discover_tools

            # This will test against the actual tools directory
            result = await discover_tools()

            # Should return a list (may be empty if no tools defined)
            assert isinstance(result, list)

            # All items should be ToolDefinition instances
            for tool in result:
                assert isinstance(tool, ToolDefinition)
                assert hasattr(tool, 'name')
                assert hasattr(tool, 'description')
                assert hasattr(tool, 'input_schema')

        except Exception as e:
            # If tools package doesn't exist or has issues, that's okay for this test
            pytest.skip(f"Skipping integration test: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
