"""
Core types and enums for Ollama MCP Server
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ResponseFormat(str, Enum):
    """Response format for tool outputs"""

    MARKDOWN = "markdown"
    JSON = "json"


class GenerationOptions(BaseModel):
    """Generation options that can be passed to Ollama models"""

    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    num_predict: Optional[int] = None
    repeat_penalty: Optional[float] = None
    seed: Optional[int] = None
    stop: Optional[List[str]] = None


class MessageRole(str, Enum):
    """Message role for chat"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    """Chat message structure"""

    role: MessageRole
    content: str
    images: Optional[List[str]] = None
    tool_calls: Optional[List["ToolCall"]] = None


class Tool(BaseModel):
    """Tool definition for function calling"""

    type: str
    function: Dict[str, Any]


class ToolCall(BaseModel):
    """Tool call made by the model"""

    function: Dict[str, Any]


class ToolDefinition(BaseModel):
    """Represents a tool's metadata and handler function"""

    name: str
    description: str
    input_schema: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}}
    )


class ToolContext(BaseModel):
    """Base tool context passed to all tool implementations"""

    pass  # In Python, we'll use dependency injection


class ToolResult(BaseModel):
    """Tool result with content and format"""

    content: str
    format: ResponseFormat


# Error types
class OllamaError(Exception):
    """Base error for Ollama operations"""

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class ModelNotFoundError(OllamaError):
    """Error when a model is not found"""

    def __init__(self, model_name: str):
        super().__init__(
            f"Model not found: {model_name}. Use ollama_list to see available models."
        )


class NetworkError(OllamaError):
    """Network-related error"""

    pass


class WebSearchResult(BaseModel):
    """Web search result"""

    title: str
    url: str
    content: str


class WebFetchResult(BaseModel):
    """Web fetch result"""

    title: str
    content: str
    links: List[str]
