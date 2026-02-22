"""
Core types and enums for Ollama MCP Server
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ResponseFormat(str, Enum):
    """Response format for tool outputs"""

    MARKDOWN = "markdown"
    JSON = "json"


class GenerationOptions(BaseModel):
    """
    Generation options that can be passed to Ollama models.

    All parameters are optional and will use model defaults if not specified.
    """

    temperature: Optional[float] = Field(
        None,
        description="Controls randomness in generation (0.0 = deterministic, higher = more random)",
        ge=0.0,
    )
    top_p: Optional[float] = Field(
        None,
        description="Nucleus sampling threshold (0.0-1.0)",
        ge=0.0,
        le=1.0,
    )
    top_k: Optional[int] = Field(
        None,
        description="Limits vocabulary to top K tokens",
        gt=0,
    )
    num_predict: Optional[int] = Field(
        None,
        description="Maximum number of tokens to generate",
        gt=0,
    )
    repeat_penalty: Optional[float] = Field(
        None,
        description="Penalty for repeating tokens (1.0 = no penalty)",
        ge=0.0,
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducible generation",
        ge=0,
    )
    stop: Optional[List[str]] = Field(
        None,
        description="List of strings that will stop generation when encountered",
    )


class MessageRole(str, Enum):
    """Message role for chat"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ToolFunction(BaseModel):
    """
    Function definition within a tool.

    Defines the function name, description, and parameters schema.
    """

    name: str = Field(description="Name of the function")
    description: str = Field(description="Description of what the function does")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON Schema describing the function parameters",
    )


class Tool(BaseModel):
    """
    Tool definition for function calling.

    Represents a tool that can be called by the model during generation.
    """

    type: str = Field(description="Type of tool (typically 'function')")
    function: ToolFunction = Field(description="Function definition")


class ToolCallFunction(BaseModel):
    """
    Function call details within a tool call.

    Contains the function name and arguments.
    """

    name: str = Field(description="Name of the function being called")
    arguments: str = Field(
        description="JSON string of function arguments",
    )


class ToolCall(BaseModel):
    """
    Tool call made by the model.

    Represents a request from the model to execute a specific tool/function.
    """

    function: ToolCallFunction = Field(description="Function call details")


class ChatMessage(BaseModel):
    """
    Chat message structure for conversation history.

    Represents a single message in a chat conversation with role, content,
    and optional images or tool calls.
    """

    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="Text content of the message")
    images: Optional[List[str]] = Field(
        None,
        description="Optional list of base64-encoded images or image URLs",
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        None,
        description="Optional list of tool calls made by the assistant",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate that content is not empty."""
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v


class ToolDefinition(BaseModel):
    """
    Represents a tool's metadata and handler function.

    Used internally to register and manage available tools.
    """

    name: str = Field(description="Unique name of the tool")
    description: str = Field(description="Human-readable description of the tool")
    input_schema: Dict[str, Any] = Field(
        default_factory=lambda: {"type": "object", "properties": {}},
        description="JSON Schema defining the tool's input parameters",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that tool name is not empty and contains valid characters."""
        if not v or not v.strip():
            raise ValueError("Tool name cannot be empty")
        if not v[0].isalnum():
            raise ValueError("Tool name must start with an alphanumeric character")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Tool name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v


class ToolContext(BaseModel):
    """
    Base tool context passed to all tool implementations.

    This class can be extended to include shared context like configuration,
    authentication, or other dependencies needed by tool handlers.

    Note: Currently empty as context is passed via dependency injection.
    Future extensions might include:
    - user_id: Optional[str] - User identifier for access control
    - session_id: Optional[str] - Session identifier for tracking
    - config: Optional[Dict[str, Any]] - Tool-specific configuration
    """

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields for extensibility


class ToolResult(BaseModel):
    """
    Tool result with content and format.

    Represents the output from a tool execution.
    """

    content: str = Field(description="Result content from tool execution")
    format: ResponseFormat = Field(description="Format of the result content")


# Error types
class OllamaError(Exception):
    """
    Base error for Ollama operations.

    All Ollama-specific exceptions inherit from this class.

    Args:
        message: Error message describing what went wrong
        cause: Optional underlying exception that caused this error
    """

    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause
        self.message = message

    def __str__(self) -> str:
        """String representation of the error."""
        if self.cause:
            return f"{self.message} (caused by: {self.cause})"
        return self.message


class ModelNotFoundError(OllamaError):
    """
    Error when a model is not found.

    Raised when attempting to use a model that doesn't exist locally.

    Args:
        model_name: Name of the model that was not found
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(
            f"Model not found: {model_name}. Use ollama_list to see available models."
        )


class NetworkError(OllamaError):
    """
    Network-related error.

    Raised when network communication with the Ollama server fails.
    This includes connection errors, timeouts, and other network issues.
    """

    pass


class WebSearchResult(BaseModel):
    """
    Web search result.

    Represents a single result from a web search operation.
    """

    title: str = Field(description="Title of the search result")
    url: HttpUrl = Field(description="URL of the search result")
    content: str = Field(description="Snippet or summary of the result content")

    @field_validator("title", "content")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class WebFetchResult(BaseModel):
    """
    Web fetch result.

    Represents the result of fetching and parsing a web page.
    """

    title: str = Field(description="Title of the web page")
    content: str = Field(description="Extracted text content from the page")
    links: List[HttpUrl] = Field(
        default_factory=list,
        description="List of links found on the page",
    )

    @field_validator("title", "content")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that text fields are not empty."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
