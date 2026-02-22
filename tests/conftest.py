"""
Pytest configuration and shared fixtures for mcp-ollama-python tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Package is installed, no path manipulation needed


@pytest.fixture
def mock_ollama_response_list():
    """Mock response for ollama list models"""
    return {
        "models": [
            {
                "name": "llama3.1:latest",
                "model": "llama3.1:latest",
                "modified_at": "2024-01-15T10:30:00Z",
                "size": 4661224676,
                "digest": "abc123",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "8B",
                    "quantization_level": "Q4_0"
                }
            },
            {
                "name": "mistral:latest",
                "model": "mistral:latest",
                "modified_at": "2024-01-14T08:00:00Z",
                "size": 4109865159,
                "digest": "def456",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "mistral",
                    "families": ["mistral"],
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0"
                }
            }
        ]
    }


@pytest.fixture
def mock_ollama_response_show():
    """Mock response for ollama show model"""
    return {
        "modelfile": "FROM llama3.1\nSYSTEM You are a helpful assistant.",
        "parameters": "temperature 0.7\ntop_p 0.9",
        "template": "{{ .System }}\n{{ .Prompt }}",
        "details": {
            "parent_model": "",
            "format": "gguf",
            "family": "llama",
            "families": ["llama"],
            "parameter_size": "8B",
            "quantization_level": "Q4_0"
        },
        "model_info": {
            "general.architecture": "llama",
            "general.file_type": 2,
            "general.parameter_count": 8030261248,
            "general.quantization_version": 2
        }
    }


@pytest.fixture
def mock_ollama_response_generate():
    """Mock response for ollama generate"""
    return {
        "model": "llama3.1:latest",
        "created_at": "2024-01-15T10:30:00Z",
        "response": "Hello! How can I help you today?",
        "done": True,
        "context": [1, 2, 3, 4, 5],
        "total_duration": 1500000000,
        "load_duration": 500000000,
        "prompt_eval_count": 10,
        "prompt_eval_duration": 200000000,
        "eval_count": 15,
        "eval_duration": 800000000
    }


@pytest.fixture
def mock_ollama_response_chat():
    """Mock response for ollama chat"""
    return {
        "model": "llama3.1:latest",
        "created_at": "2024-01-15T10:30:00Z",
        "message": {
            "role": "assistant",
            "content": "I'm doing well, thank you for asking! How can I assist you today?"
        },
        "done": True,
        "total_duration": 2000000000,
        "load_duration": 600000000,
        "prompt_eval_count": 20,
        "prompt_eval_duration": 300000000,
        "eval_count": 25,
        "eval_duration": 1100000000
    }


@pytest.fixture
def mock_ollama_response_ps():
    """Mock response for ollama ps (running models)"""
    return {
        "models": [
            {
                "name": "llama3.1:latest",
                "model": "llama3.1:latest",
                "size": 4661224676,
                "digest": "abc123",
                "details": {
                    "parent_model": "",
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "8B",
                    "quantization_level": "Q4_0"
                },
                "expires_at": "2024-01-15T11:30:00Z",
                "size_vram": 4661224676
            }
        ]
    }


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client"""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.aclose = AsyncMock()
    return mock_client


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing"""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]


@pytest.fixture
def sample_generation_options():
    """Sample generation options for testing"""
    return {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "num_predict": 100
    }


@pytest.fixture
def sample_tool_definition():
    """Sample tool definition for testing"""
    return {
        "name": "test_tool",
        "description": "A test tool for unit testing",
        "input_schema": {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "First parameter"
                },
                "param2": {
                    "type": "integer",
                    "description": "Second parameter"
                }
            },
            "required": ["param1"]
        }
    }
