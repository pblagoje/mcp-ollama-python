"""
Tests for server.py - MCP Server implementation for Ollama
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Package is installed, import from ollama_mcp_python
from ollama_mcp_python.models import ResponseFormat, ToolDefinition


class TestOllamaMCPServerInit:
    """Tests for OllamaMCPServer initialization"""

    def test_default_initialization(self):
        """Test default initialization creates OllamaClient"""
        with patch('ollama_mcp_python.server.OllamaClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer()
            
            assert server.ollama_client is not None

    def test_custom_client_initialization(self):
        """Test initialization with custom client"""
        mock_client = MagicMock()
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        
        assert server.ollama_client == mock_client


class TestHandleListTools:
    """Tests for handle_list_tools method"""

    @pytest.mark.asyncio
    async def test_list_tools_returns_tools(self, sample_tool_definition):
        """Test that list_tools returns discovered tools"""
        mock_tool = ToolDefinition(**sample_tool_definition)
        
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [mock_tool]
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_list_tools()
            
            assert "tools" in result
            assert len(result["tools"]) == 1
            assert result["tools"][0]["name"] == "test_tool"
            assert result["tools"][0]["description"] == "A test tool for unit testing"

    @pytest.mark.asyncio
    async def test_list_tools_empty(self):
        """Test list_tools with no tools discovered"""
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_list_tools()
            
            assert result["tools"] == []

    @pytest.mark.asyncio
    async def test_list_tools_multiple(self):
        """Test list_tools with multiple tools"""
        tools = [
            ToolDefinition(name="tool1", description="First tool", input_schema={}),
            ToolDefinition(name="tool2", description="Second tool", input_schema={}),
            ToolDefinition(name="tool3", description="Third tool", input_schema={})
        ]
        
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = tools
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_list_tools()
            
            assert len(result["tools"]) == 3


class TestHandleCallTool:
    """Tests for handle_call_tool method"""

    @pytest.mark.asyncio
    async def test_call_unknown_tool(self):
        """Test calling an unknown tool returns error"""
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = []
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=MagicMock())
            result = await server.handle_call_tool("nonexistent_tool", {})
            
            assert result.get("isError") is True
            assert "Unknown tool" in result["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mock_ollama_response_list):
        """Test successful tool call"""
        tool = ToolDefinition(
            name="ollama_list",
            description="List models",
            input_schema={}
        )
        
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=json.dumps(mock_ollama_response_list))
        
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [tool]
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=mock_client)
            result = await server.handle_call_tool("ollama_list", {})
            
            assert "content" in result
            assert result["content"][0]["type"] == "text"
            assert result.get("isError") is not True

    @pytest.mark.asyncio
    async def test_call_tool_with_format_markdown(self, mock_ollama_response_list):
        """Test tool call with markdown format"""
        tool = ToolDefinition(
            name="ollama_list",
            description="List models",
            input_schema={}
        )
        
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=json.dumps(mock_ollama_response_list))
        
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [tool]
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=mock_client)
            result = await server.handle_call_tool("ollama_list", {"format": "markdown"})
            
            assert "content" in result

    @pytest.mark.asyncio
    async def test_call_tool_exception_handling(self):
        """Test tool call handles exceptions gracefully"""
        tool = ToolDefinition(
            name="ollama_list",
            description="List models",
            input_schema={}
        )
        
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(side_effect=Exception("Connection failed"))
        
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = [tool]
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=mock_client)
            result = await server.handle_call_tool("ollama_list", {})
            
            assert result.get("isError") is True
            assert "Error:" in result["content"][0]["text"]


class TestToolHandlers:
    """Tests for individual tool handlers"""

    @pytest.mark.asyncio
    async def test_handle_list_models(self, mock_ollama_response_list):
        """Test _handle_list_models"""
        mock_client = AsyncMock()
        # format_response expects JSON string, not dict
        mock_client.list = AsyncMock(return_value=json.dumps(mock_ollama_response_list))
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_list_models(ResponseFormat.JSON)
        
        # Result should be JSON string
        parsed = json.loads(result)
        assert "models" in parsed

    @pytest.mark.asyncio
    async def test_handle_show_model(self, mock_ollama_response_show):
        """Test _handle_show_model"""
        mock_client = AsyncMock()
        mock_client.show = AsyncMock(return_value=json.dumps(mock_ollama_response_show))
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_show_model(
            {"model": "llama3.1:latest"}, 
            ResponseFormat.JSON
        )
        
        mock_client.show.assert_called_once_with("llama3.1:latest")

    @pytest.mark.asyncio
    async def test_handle_show_model_missing_name(self):
        """Test _handle_show_model raises error for missing model name"""
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        
        with pytest.raises(ValueError) as exc_info:
            await server._handle_show_model({}, ResponseFormat.JSON)
        
        assert "Model name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_generate(self, mock_ollama_response_generate):
        """Test _handle_generate"""
        mock_client = AsyncMock()
        mock_client.generate = AsyncMock(return_value=json.dumps(mock_ollama_response_generate))
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_generate(
            {"model": "llama3.1", "prompt": "Hello"},
            ResponseFormat.JSON
        )
        
        mock_client.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_generate_missing_model(self):
        """Test _handle_generate raises error for missing model"""
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        
        with pytest.raises(ValueError) as exc_info:
            await server._handle_generate({"prompt": "Hello"}, ResponseFormat.JSON)
        
        assert "Model name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_generate_missing_prompt(self):
        """Test _handle_generate raises error for missing prompt"""
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        
        with pytest.raises(ValueError) as exc_info:
            await server._handle_generate({"model": "llama3.1"}, ResponseFormat.JSON)
        
        assert "Prompt is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_chat(self, mock_ollama_response_chat):
        """Test _handle_chat"""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=json.dumps(mock_ollama_response_chat))
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_chat(
            {
                "model": "llama3.1",
                "messages": [{"role": "user", "content": "Hello"}]
            },
            ResponseFormat.JSON
        )
        
        mock_client.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_chat_missing_messages(self):
        """Test _handle_chat raises error for missing messages"""
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        
        with pytest.raises(ValueError) as exc_info:
            await server._handle_chat({"model": "llama3.1"}, ResponseFormat.JSON)
        
        assert "Messages are required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_handle_pull_model(self):
        """Test _handle_pull_model"""
        mock_client = AsyncMock()
        mock_client.pull = AsyncMock(return_value='{"status": "success"}')
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_pull_model(
            {"model": "llama3.1"},
            ResponseFormat.JSON
        )
        
        mock_client.pull.assert_called_once_with("llama3.1")

    @pytest.mark.asyncio
    async def test_handle_delete_model(self):
        """Test _handle_delete_model"""
        mock_client = AsyncMock()
        mock_client.delete = AsyncMock(return_value='{"status": "success"}')
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_delete_model(
            {"model": "old-model"},
            ResponseFormat.JSON
        )
        
        mock_client.delete.assert_called_once_with("old-model")

    @pytest.mark.asyncio
    async def test_handle_ps(self, mock_ollama_response_ps):
        """Test _handle_ps"""
        mock_client = AsyncMock()
        mock_client.ps = AsyncMock(return_value=json.dumps(mock_ollama_response_ps))
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._handle_ps(ResponseFormat.JSON)
        
        mock_client.ps.assert_called_once()


class TestExecuteToolHandler:
    """Tests for _execute_tool_handler method"""

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing unknown tool raises error"""
        unknown_tool = ToolDefinition(
            name="unknown_tool",
            description="Unknown",
            input_schema={}
        )
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=MagicMock())
        
        with pytest.raises(ValueError) as exc_info:
            await server._execute_tool_handler(unknown_tool, {}, ResponseFormat.JSON)
        
        assert "not implemented" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execute_ollama_list(self, mock_ollama_response_list):
        """Test executing ollama_list tool"""
        tool = ToolDefinition(
            name="ollama_list",
            description="List models",
            input_schema={}
        )
        
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=json.dumps(mock_ollama_response_list))
        
        from ollama_mcp_python.server import OllamaMCPServer
        server = OllamaMCPServer(ollama_client=mock_client)
        result = await server._execute_tool_handler(tool, {}, ResponseFormat.JSON)
        
        assert result is not None


class TestIntegration:
    """Integration tests for the server"""

    @pytest.mark.asyncio
    async def test_full_list_and_call_flow(self, mock_ollama_response_list):
        """Test complete flow of listing tools and calling one"""
        # Setup mock tools
        tools = [
            ToolDefinition(name="ollama_list", description="List models", input_schema={}),
            ToolDefinition(name="ollama_show", description="Show model", input_schema={
                "type": "object",
                "properties": {"model": {"type": "string"}},
                "required": ["model"]
            })
        ]
        
        mock_client = AsyncMock()
        mock_client.list = AsyncMock(return_value=json.dumps(mock_ollama_response_list))
        
        with patch('ollama_mcp_python.server.discover_tools', new_callable=AsyncMock) as mock_discover:
            mock_discover.return_value = tools
            
            from ollama_mcp_python.server import OllamaMCPServer
            server = OllamaMCPServer(ollama_client=mock_client)
            
            # List tools
            list_result = await server.handle_list_tools()
            assert len(list_result["tools"]) == 2
            
            # Call a tool
            call_result = await server.handle_call_tool("ollama_list", {})
            assert "content" in call_result
            assert call_result.get("isError") is not True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
