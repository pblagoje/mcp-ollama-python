"""
Tests for ollama_client.py - Ollama HTTP client wrapper
"""

import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

# Package is installed, import from mcp_ollama_python
from mcp_ollama_python.models import GenerationOptions, ChatMessage, MessageRole, Tool


class TestOllamaClientInit:
    """Tests for OllamaClient initialization"""

    def test_default_initialization(self):
        """Test default initialization uses environment or defaults"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('httpx.AsyncClient') as mock_client:
                from mcp_ollama_python.ollama_client import OllamaClient
                client = OllamaClient()
                assert client.host == "http://127.0.0.1:11434"
                assert client.api_key is None

    def test_custom_host(self):
        """Test initialization with custom host"""
        with patch('httpx.AsyncClient') as mock_client:
            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient(host="http://custom:8080")
            assert client.host == "http://custom:8080"

    def test_environment_host(self):
        """Test initialization reads OLLAMA_HOST from environment"""
        with patch.dict(os.environ, {"OLLAMA_HOST": "http://env-host:11434"}):
            with patch('httpx.AsyncClient') as mock_client:
                # Need to reimport to pick up env var
                import importlib
                from mcp_ollama_python import ollama_client
                importlib.reload(ollama_client)
                client = ollama_client.OllamaClient()
                assert client.host == "http://env-host:11434"

    def test_api_key_in_headers(self):
        """Test API key is added to headers"""
        with patch('httpx.AsyncClient') as mock_client:
            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient(api_key="test-key")
            assert client.api_key == "test-key"
            # Check that AsyncClient was called with headers containing auth
            call_kwargs = mock_client.call_args.kwargs
            assert "headers" in call_kwargs
            assert call_kwargs["headers"].get("Authorization") == "Bearer test-key"


class TestOllamaClientContextManager:
    """Tests for async context manager"""

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self):
        """Test context manager properly closes client"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            async with OllamaClient() as client:
                pass

            mock_client.aclose.assert_called_once()


class TestOllamaClientPost:
    """Tests for _post method"""

    @pytest.mark.asyncio
    async def test_post_success(self):
        """Test successful POST request"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": "success"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client._post("/api/test", {"key": "value"})

            assert result == {"result": "success"}
            mock_client.post.assert_called_once_with("/api/test", json={"key": "value"})

    @pytest.mark.asyncio
    async def test_post_http_error(self):
        """Test POST request with HTTP error"""
        import httpx

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Error", request=MagicMock(), response=mock_response
            )

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()

            with pytest.raises(Exception) as exc_info:
                await client._post("/api/test", {})

            assert "Ollama API error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_post_connection_error(self):
        """Test POST request with connection error"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()

            with pytest.raises(Exception) as exc_info:
                await client._post("/api/test", {})

            assert "Failed to connect to Ollama" in str(exc_info.value)


class TestOllamaClientListModels:
    """Tests for list method"""

    @pytest.mark.asyncio
    async def test_list_models(self, mock_ollama_response_list):
        """Test listing models"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_list
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.list()

            assert "models" in result
            assert len(result["models"]) == 2
            mock_client.get.assert_called_once_with("/api/tags")


class TestOllamaClientShowModel:
    """Tests for show method"""

    @pytest.mark.asyncio
    async def test_show_model(self, mock_ollama_response_show):
        """Test showing model information"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_show
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.show("llama3.1:latest")

            assert "modelfile" in result
            assert "details" in result
            mock_client.post.assert_called_once_with("/api/show", json={"name": "llama3.1:latest"})


class TestOllamaClientGenerate:
    """Tests for generate method"""

    @pytest.mark.asyncio
    async def test_generate_basic(self, mock_ollama_response_generate):
        """Test basic text generation"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_generate
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.generate("llama3.1", "Hello")

            assert "response" in result
            assert result["done"] is True

    @pytest.mark.asyncio
    async def test_generate_with_options(self, mock_ollama_response_generate):
        """Test generation with options"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_generate
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()

            options = GenerationOptions(temperature=0.7, top_p=0.9)
            result = await client.generate("llama3.1", "Hello", options=options)

            # Verify options were passed
            call_args = mock_client.post.call_args
            assert "options" in call_args.kwargs["json"]


class TestOllamaClientChat:
    """Tests for chat method"""

    @pytest.mark.asyncio
    async def test_chat_basic(self, mock_ollama_response_chat):
        """Test basic chat"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_chat
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()

            messages = [ChatMessage(role=MessageRole.USER, content="Hello")]
            result = await client.chat("llama3.1", messages)

            assert "message" in result
            assert result["message"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, mock_ollama_response_chat):
        """Test chat with system message"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_chat
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()

            messages = [
                ChatMessage(role=MessageRole.SYSTEM, content="You are helpful"),
                ChatMessage(role=MessageRole.USER, content="Hello")
            ]
            result = await client.chat("llama3.1", messages)

            # Verify messages were serialized
            call_args = mock_client.post.call_args
            sent_messages = call_args.kwargs["json"]["messages"]
            assert len(sent_messages) == 2


class TestOllamaClientModelManagement:
    """Tests for model management methods"""

    @pytest.mark.asyncio
    async def test_pull_model(self):
        """Test pulling a model"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "success"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.pull("llama3.1")

            mock_client.post.assert_called_once_with("/api/pull", json={"name": "llama3.1", "stream": False})

    @pytest.mark.asyncio
    async def test_delete_model(self):
        """Test deleting a model"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "success"}
            mock_response.raise_for_status = MagicMock()
            mock_response.headers = {"content-length": "0"}
            mock_response.content = b""

            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.delete("old-model")

            mock_client.request.assert_called_once_with(
                "DELETE", "/api/delete", json={"name": "old-model"}
            )
            assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_copy_model(self):
        """Test copying a model"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"status": "success"}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.copy("source-model", "dest-model")

            mock_client.post.assert_called_once_with(
                "/api/copy",
                json={"source": "source-model", "destination": "dest-model"}
            )

    @pytest.mark.asyncio
    async def test_ps(self, mock_ollama_response_ps):
        """Test listing running models"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_ollama_response_ps
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.ps()

            assert "models" in result
            mock_client.get.assert_called_once_with("/api/ps")


class TestOllamaClientEmbeddings:
    """Tests for embed method"""

    @pytest.mark.asyncio
    async def test_embed_single_text(self):
        """Test embedding single text"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.embed("nomic-embed-text", "Hello world")

            assert "embeddings" in result
            mock_client.post.assert_called_once_with(
                "/api/embed",
                json={"model": "nomic-embed-text", "input": "Hello world"}
            )

    @pytest.mark.asyncio
    async def test_embed_multiple_texts(self):
        """Test embedding multiple texts"""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "embeddings": [[0.1, 0.2], [0.3, 0.4]]
            }
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            from mcp_ollama_python.ollama_client import OllamaClient
            client = OllamaClient()
            result = await client.embed("nomic-embed-text", ["Text 1", "Text 2"])

            assert len(result["embeddings"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
