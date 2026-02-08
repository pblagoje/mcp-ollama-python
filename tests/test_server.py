"""
Tests for server.py - MCP Server implementation for Ollama
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Package is installed, import from mcp_ollama_python
from mcp_ollama_python.models import ResponseFormat, ToolDefinition
from mcp_ollama_python.autoloader import ToolRegistry


def _make_registry(tools_and_handlers):
    """Helper to build a ToolRegistry from a list of (ToolDefinition, handler) tuples."""
    registry = ToolRegistry()
    for tool_def, handler in tools_and_handlers:
        registry.register(tool_def, handler)
    return registry


def _make_registry_from_tools(tools):
    """Helper to build a ToolRegistry from ToolDefinitions with no-op handlers."""
    registry = ToolRegistry()
    for tool_def in tools:
        async def _noop(client, args, fmt):
            return "{}"
        registry.register(tool_def, _noop)
    return registry


class TestOllamaMCPServerInit:
    """Tests for OllamaMCPServer initialization"""

    def test_default_initialization(self):
        """Test default initialization creates OllamaClient"""
        with patch('mcp_ollama_python.server.OllamaClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer()

            assert server.ollama_client is not None

    def test_custom_client_initialization(self):
        """Test initialization with custom client"""
        mock_client = MagicMock()

        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)

        assert server.ollama_client == mock_client

    def test_resources_initialized(self):
        """Test default resources are created on init"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())

        assert "ollama://models" in server._resources
        assert "ollama://running" in server._resources
        assert "ollama://config" in server._resources

    def test_prompts_initialized(self):
        """Test default prompts are created on init"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())

        assert "explain_lora" in server._prompts
        assert "code_review" in server._prompts
        assert "hello_world" in server._prompts


class TestHandleListTools:
    """Tests for handle_list_tools method"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self, sample_tool_definition):
        """Test that list_tools returns discovered tools"""
        mock_tool = ToolDefinition(**sample_tool_definition)
        mock_handler = AsyncMock(return_value="{}")
        registry = _make_registry([(mock_tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_list_tools()

            assert "tools" in result
            assert len(result["tools"]) == 1
            assert result["tools"][0]["name"] == "test_tool"
            assert result["tools"][0]["description"] == "A test tool for unit testing"

    @pytest.mark.asyncio
    async def test_list_tools_empty(self):
        """Test list_tools with no tools discovered"""
        registry = ToolRegistry()

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_list_tools()

            assert result["tools"] == []

    @pytest.mark.asyncio
    async def test_list_tools_multiple(self):
        """Test list_tools with multiple tools"""
        tools = [
            ToolDefinition(name="tool1", description="First tool"),
            ToolDefinition(name="tool2", description="Second tool"),
            ToolDefinition(name="tool3", description="Third tool"),
        ]
        registry = _make_registry_from_tools(tools)

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_list_tools()

            assert len(result["tools"]) == 3

    @pytest.mark.asyncio
    async def test_list_tools_caches_registry(self):
        """Test that tool registry is cached after first call"""
        registry = ToolRegistry()

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            await server.handle_list_tools()
            await server.handle_list_tools()

            # discover_tools_with_handlers should only be called once due to caching
            mock_discover.assert_called_once()


class TestHandleCallTool:
    """Tests for handle_call_tool method"""

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test calling an unknown tool returns error"""
        registry = ToolRegistry()

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("nonexistent_tool", {})

            assert result.get("isError") is True
            assert "Unknown tool" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_tool_success(self):
        """Test successful tool call"""
        tool = ToolDefinition(name="ollama_list", description="List models")
        mock_handler = AsyncMock(return_value='{"models": []}')
        registry = _make_registry([(tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("ollama_list", {})

            assert "content" in result
            assert result["content"][0]["type"] == "text"
            assert result.get("isError") is not True
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_passes_format(self):
        """Test tool call passes the correct format to handler"""
        tool = ToolDefinition(name="ollama_list", description="List models")
        mock_handler = AsyncMock(return_value="# Models")
        registry = _make_registry([(tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("ollama_list", {"format": "markdown"})

            assert "content" in result
            # Verify handler was called with markdown format
            call_args = mock_handler.call_args
            assert call_args[0][2] == ResponseFormat.MARKDOWN

    @pytest.mark.asyncio
    async def test_call_tool_default_format_is_json(self):
        """Test tool call defaults to JSON format"""
        tool = ToolDefinition(name="ollama_list", description="List models")
        mock_handler = AsyncMock(return_value='{}')
        registry = _make_registry([(tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            await server.handle_call_tool("ollama_list", {})

            call_args = mock_handler.call_args
            assert call_args[0][2] == ResponseFormat.JSON

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(self):
        """Test tool call handles exceptions gracefully"""
        tool = ToolDefinition(name="ollama_list", description="List models")
        mock_handler = AsyncMock(side_effect=Exception("Connection failed"))
        registry = _make_registry([(tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("ollama_list", {})

            assert result.get("isError") is True
            assert "Error:" in result["content"][0]["text"]
            assert "Connection failed" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_tool_structured_content_for_json(self):
        """Test tool call includes structuredContent when result is valid JSON"""
        tool = ToolDefinition(name="test_tool", description="Test")
        mock_handler = AsyncMock(return_value='{"key": "value"}')
        registry = _make_registry([(tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("test_tool", {})

            assert result["structuredContent"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_call_tool_no_structured_content_for_non_json(self):
        """Test tool call sets structuredContent to None for non-JSON results"""
        tool = ToolDefinition(name="test_tool", description="Test")
        mock_handler = AsyncMock(return_value="plain text result")
        registry = _make_registry([(tool, mock_handler)])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("test_tool", {})

            assert result["structuredContent"] is None


class TestHandleResources:
    """Tests for resource handling methods"""

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test listing available resources"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        result = await server.handle_list_resources()

        assert "resources" in result
        resource_uris = [r["uri"] for r in result["resources"]]
        assert "ollama://models" in resource_uris
        assert "ollama://running" in resource_uris
        assert "ollama://config" in resource_uris

    @pytest.mark.asyncio
    async def test_read_resource_models(self, mock_ollama_response_list):
        """Test reading the models resource"""
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=mock_ollama_response_list)

        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server.handle_read_resource("ollama://models")

        assert "contents" in result
        content_text = result["contents"][0]["text"]
        parsed = json.loads(content_text)
        assert "models" in parsed

    @pytest.mark.asyncio
    async def test_read_resource_config(self):
        """Test reading the config resource"""
        mock_client = MagicMock()
        mock_client.host = "http://127.0.0.1:11434"
        mock_client.api_key = None

        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server.handle_read_resource("ollama://config")

        content_text = result["contents"][0]["text"]
        parsed = json.loads(content_text)
        assert parsed["host"] == "http://127.0.0.1:11434"
        assert parsed["has_api_key"] is False

    @pytest.mark.asyncio
    async def test_read_resource_unknown(self):
        """Test reading an unknown resource returns error"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        result = await server.handle_read_resource("ollama://unknown")

        assert result.get("isError") is True
        assert "Unknown resource" in result["contents"][0]["text"]


class TestHandlePrompts:
    """Tests for prompt handling methods"""

    @pytest.mark.asyncio
    async def test_list_prompts(self):
        """Test listing available prompts"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        result = await server.handle_list_prompts()

        assert "prompts" in result
        prompt_names = [p["name"] for p in result["prompts"]]
        assert "explain_lora" in prompt_names
        assert "code_review" in prompt_names
        assert "hello_world" in prompt_names

    @pytest.mark.asyncio
    async def test_get_prompt_explain_lora(self):
        """Test getting explain_lora prompt"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        result = await server.handle_get_prompt("explain_lora", {"detail_level": "advanced"})

        assert "messages" in result
        assert "advanced" in result["messages"][0]["content"]["text"]

    @pytest.mark.asyncio
    async def test_get_prompt_hello_world(self):
        """Test getting hello_world prompt"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        result = await server.handle_get_prompt("hello_world", {"language": "Rust"})

        assert "Rust" in result["messages"][0]["content"]["text"]

    @pytest.mark.asyncio
    async def test_get_prompt_unknown(self):
        """Test getting unknown prompt raises error"""
        from mcp_ollama_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())

        with pytest.raises(ValueError) as exc_info:
            await server.handle_get_prompt("nonexistent", {})

        assert "Unknown prompt" in str(exc_info.value)


class TestIntegration:
    """Integration tests for the server"""

    @pytest.mark.asyncio
    async def test_full_list_and_call_flow(self):
        """Test complete flow of listing tools and calling one"""
        list_tool = ToolDefinition(name="ollama_list", description="List models")
        show_tool = ToolDefinition(name="ollama_show", description="Show model", input_schema={
            "type": "object",
            "properties": {"model": {"type": "string"}},
            "required": ["model"]
        })

        list_handler = AsyncMock(return_value='{"models": []}')
        show_handler = AsyncMock(return_value='{"details": {}}')
        registry = _make_registry([
            (list_tool, list_handler),
            (show_tool, show_handler),
        ])

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())

            # List tools
            list_result = await server.handle_list_tools()
            assert len(list_result["tools"]) == 2

            # Call a tool
            call_result = await server.handle_call_tool("ollama_list", {})
            assert "content" in call_result
            assert call_result.get("isError") is not True
            list_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_tool_passes_client_and_args(self):
        """Test that handle_call_tool passes ollama_client and args to handler"""
        tool = ToolDefinition(name="ollama_generate", description="Generate text")
        mock_handler = AsyncMock(return_value='{"response": "hello"}')
        registry = _make_registry([(tool, mock_handler)])

        mock_client = MagicMock()

        with patch('mcp_ollama_python.server.discover_tools_with_handlers', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = registry

            from mcp_ollama_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=mock_client)

            args = {"model": "llama3.1", "prompt": "Hello"}
            await server.handle_call_tool("ollama_generate", args)

            # Handler receives (ollama_client, args, format)
            call_args = mock_handler.call_args[0]
            assert call_args[0] is mock_client
            assert call_args[1] is args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
