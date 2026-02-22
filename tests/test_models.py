"""
Tests for models.py - Core types and enums
"""

import pytest

# Package is installed, import from mcp_ollama_python
from mcp_ollama_python.models import (
    ResponseFormat,
    GenerationOptions,
    MessageRole,
    ChatMessage,
    Tool,
    ToolFunction,
    ToolCall,
    ToolCallFunction,
    ToolDefinition,
    ToolContext,
    ToolResult,
    OllamaError,
    ModelNotFoundError,
    NetworkError,
    WebSearchResult,
    WebFetchResult
)


class TestResponseFormat:
    """Tests for ResponseFormat enum"""

    def test_markdown_format(self):
        """Test MARKDOWN format value"""
        assert ResponseFormat.MARKDOWN.value == "markdown"
        assert ResponseFormat.MARKDOWN == "markdown"

    def test_json_format(self):
        """Test JSON format value"""
        assert ResponseFormat.JSON.value == "json"
        assert ResponseFormat.JSON == "json"

    def test_enum_membership(self):
        """Test enum membership"""
        assert ResponseFormat.MARKDOWN in ResponseFormat
        assert ResponseFormat.JSON in ResponseFormat


class TestGenerationOptions:
    """Tests for GenerationOptions model"""

    def test_default_initialization(self):
        """Test default initialization with no parameters"""
        options = GenerationOptions()
        assert options.temperature is None
        assert options.top_p is None
        assert options.top_k is None
        assert options.num_predict is None
        assert options.repeat_penalty is None
        assert options.seed is None
        assert options.stop is None

    def test_full_initialization(self):
        """Test initialization with all parameters"""
        options = GenerationOptions(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            num_predict=100,
            repeat_penalty=1.1,
            seed=42,
            stop=["END", "STOP"]
        )
        assert options.temperature == 0.7
        assert options.top_p == 0.9
        assert options.top_k == 40
        assert options.num_predict == 100
        assert options.repeat_penalty == 1.1
        assert options.seed == 42
        assert options.stop == ["END", "STOP"]

    def test_partial_initialization(self):
        """Test initialization with partial parameters"""
        options = GenerationOptions(temperature=0.5, top_k=20)
        assert options.temperature == 0.5
        assert options.top_k == 20
        assert options.top_p is None

    def test_model_dump(self):
        """Test model serialization"""
        options = GenerationOptions(temperature=0.7, top_p=0.9)
        dumped = options.model_dump(exclude_unset=True)
        assert dumped == {"temperature": 0.7, "top_p": 0.9}


class TestMessageRole:
    """Tests for MessageRole enum"""

    def test_system_role(self):
        """Test SYSTEM role"""
        assert MessageRole.SYSTEM.value == "system"

    def test_user_role(self):
        """Test USER role"""
        assert MessageRole.USER.value == "user"

    def test_assistant_role(self):
        """Test ASSISTANT role"""
        assert MessageRole.ASSISTANT.value == "assistant"


class TestChatMessage:
    """Tests for ChatMessage model"""

    def test_basic_message(self):
        """Test basic message creation"""
        msg = ChatMessage(role=MessageRole.USER, content="Hello!")
        assert msg.role == MessageRole.USER
        assert msg.content == "Hello!"
        assert msg.images is None
        assert msg.tool_calls is None

    def test_message_with_images(self):
        """Test message with images"""
        msg = ChatMessage(
            role=MessageRole.USER,
            content="What's in this image?",
            images=["base64_encoded_image_data"]
        )
        assert msg.images == ["base64_encoded_image_data"]

    def test_system_message(self):
        """Test system message"""
        msg = ChatMessage(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant."
        )
        assert msg.role == MessageRole.SYSTEM

    def test_message_serialization(self):
        """Test message serialization"""
        msg = ChatMessage(role=MessageRole.USER, content="Test")
        dumped = msg.model_dump(exclude_unset=True)
        assert "role" in dumped
        assert "content" in dumped


class TestTool:
    """Tests for Tool model"""

    def test_tool_creation(self):
        """Test tool creation"""
        tool_function = ToolFunction(
            name="get_weather",
            description="Get weather information",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string"}
                }
            }
        )
        tool = Tool(
            type="function",
            function=tool_function
        )
        assert tool.type == "function"
        assert tool.function.name == "get_weather"
        assert tool.function.description == "Get weather information"


class TestToolCall:
    """Tests for ToolCall model"""

    def test_tool_call_creation(self):
        """Test tool call creation"""
        tool_call_function = ToolCallFunction(
            name="get_weather",
            arguments='{"location": "New York"}'
        )
        call = ToolCall(function=tool_call_function)
        assert call.function.name == "get_weather"
        assert call.function.arguments == '{"location": "New York"}'


class TestToolDefinition:
    """Tests for ToolDefinition model"""

    def test_tool_definition_creation(self):
        """Test tool definition creation"""
        tool_def = ToolDefinition(
            name="test_tool",
            description="A test tool",
            input_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        )
        assert tool_def.name == "test_tool"
        assert tool_def.description == "A test tool"
        assert "properties" in tool_def.input_schema

    def test_tool_definition_empty_schema(self):
        """Test tool definition with empty schema"""
        tool_def = ToolDefinition(
            name="simple_tool",
            description="Simple tool",
            input_schema={}
        )
        assert tool_def.input_schema == {}


class TestToolResult:
    """Tests for ToolResult model"""

    def test_tool_result_creation(self):
        """Test tool result creation"""
        result = ToolResult(
            content="Result content",
            format=ResponseFormat.JSON
        )
        assert result.content == "Result content"
        assert result.format == ResponseFormat.JSON


class TestOllamaErrors:
    """Tests for error classes"""

    def test_ollama_error(self):
        """Test base OllamaError"""
        error = OllamaError("Test error")
        assert str(error) == "Test error"
        assert error.cause is None

    def test_ollama_error_with_cause(self):
        """Test OllamaError with cause"""
        cause = ValueError("Original error")
        error = OllamaError("Wrapper error", cause=cause)
        assert error.cause == cause

    def test_model_not_found_error(self):
        """Test ModelNotFoundError"""
        error = ModelNotFoundError("nonexistent-model")
        assert "nonexistent-model" in str(error)
        assert "ollama_list" in str(error)

    def test_network_error(self):
        """Test NetworkError"""
        error = NetworkError("Connection refused")
        assert str(error) == "Connection refused"


class TestWebSearchResult:
    """Tests for WebSearchResult model"""

    def test_web_search_result_creation(self):
        """Test web search result creation"""
        result = WebSearchResult(
            title="Test Page",
            url="https://example.com",
            content="Page content here"
        )
        assert result.title == "Test Page"
        assert result.url == "https://example.com"
        assert result.content == "Page content here"


class TestWebFetchResult:
    """Tests for WebFetchResult model"""

    def test_web_fetch_result_creation(self):
        """Test web fetch result creation"""
        result = WebFetchResult(
            title="Fetched Page",
            content="Main content",
            links=["https://link1.com", "https://link2.com"]
        )
        assert result.title == "Fetched Page"
        assert result.content == "Main content"
        assert len(result.links) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
