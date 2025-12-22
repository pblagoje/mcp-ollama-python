"""
Ollama chat tool
"""

from typing import Dict, Any, List
from ..models import ToolDefinition, ResponseFormat, ChatMessage, Tool as OllamaTool, GenerationOptions, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def chat_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Interactive chat with models (supports tools/functions)"""
    model = args.get("model")
    messages = args.get("messages")
    tools = args.get("tools")
    options = args.get("options")

    if not model:
        raise ValueError("Model name is required")
    if not messages:
        raise ValueError("Messages are required")

    try:
        # Convert messages to ChatMessage objects
        chat_messages = []
        for msg in messages:
            chat_messages.append(ChatMessage(**msg))

        # Convert tools if provided
        chat_tools = None
        if tools:
            chat_tools = []
            for tool in tools:
                chat_tools.append(OllamaTool(**tool))

        # Convert options if provided
        gen_options = None
        if options:
            gen_options = GenerationOptions(**options)

        result = await ollama.chat(model, chat_messages, chat_tools, gen_options)
        return format_response(result, format)
    except Exception as e:
        if "model not found" in str(e).lower():
            raise ModelNotFoundError(model)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_chat",
    description="Interactive chat with Ollama models. Supports multi-turn conversations, tool calling, and structured outputs.",
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Name of the model to use for chat",
            },
            "messages": {
                "type": "array",
                "description": "Array of chat messages",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {
                            "type": "string",
                            "enum": ["system", "user", "assistant"],
                        },
                        "content": {
                            "type": "string",
                        },
                        "images": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["role", "content"],
                },
            },
            "tools": {
                "type": "array",
                "description": "Array of tools available to the model",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "function": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "parameters": {"type": "object"},
                            },
                        },
                    },
                },
            },
            "options": {
                "type": "object",
                "description": "Generation options (temperature, top_p, etc.)",
                "properties": {
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                    "top_p": {"type": "number", "minimum": 0, "maximum": 1},
                    "top_k": {"type": "integer", "minimum": 0},
                    "num_predict": {"type": "integer", "minimum": 1},
                    "repeat_penalty": {"type": "number", "minimum": 0},
                    "seed": {"type": "integer"},
                    "stop": {"type": "array", "items": {"type": "string"}},
                },
            },
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            },
        },
        "required": ["model", "messages"],
    },
)
