"""
Ollama chat tool
"""

import logging
from typing import Dict, Any, List, Optional
from ..models import (
    ToolDefinition,
    ResponseFormat,
    ChatMessage,
    Tool as OllamaTool,
    GenerationOptions,
    ModelNotFoundError,
)
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def chat_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Interactive chat with Ollama models.

    Supports multi-turn conversations, tool calling, and structured outputs.

    Args:
        ollama: Ollama client instance
        args: Arguments containing model, messages, tools, and options
        format: Response format (JSON or Markdown)

    Returns:
        Formatted chat response as string

    Raises:
        ValueError: If required arguments are missing or invalid
        ModelNotFoundError: If the specified model is not found
    """
    model = args.get("model")
    messages = args.get("messages")
    tools = args.get("tools")
    options = args.get("options")

    # Validate required arguments
    if not model:
        logger.error("Chat handler called without model name")
        raise ValueError("Model name is required")
    if not messages:
        logger.error("Chat handler called without messages")
        raise ValueError("Messages are required")
    if not isinstance(messages, list) or len(messages) == 0:
        logger.error("Invalid messages format: %s", type(messages))
        raise ValueError("Messages must be a non-empty list")

    logger.debug(
        "Chat handler called with model: %s, %d messages", model, len(messages)
    )

    try:
        # Convert messages to ChatMessage objects
        chat_messages: List[ChatMessage] = []
        for i, msg in enumerate(messages):
            try:
                chat_messages.append(ChatMessage(**msg))
            except Exception as e:
                logger.error("Failed to parse message %d: %s", i, e)
                raise ValueError(f"Invalid message at index {i}: {e}")

        # Convert tools if provided
        chat_tools: Optional[List[OllamaTool]] = None
        if tools:
            chat_tools = []
            for i, tool in enumerate(tools):
                try:
                    chat_tools.append(OllamaTool(**tool))
                except Exception as e:
                    logger.error("Failed to parse tool %d: %s", i, e)
                    raise ValueError(f"Invalid tool at index {i}: {e}")
            logger.debug("Using %d tools", len(chat_tools))

        # Convert options if provided
        gen_options: Optional[GenerationOptions] = None
        if options:
            try:
                gen_options = GenerationOptions(**options)
                logger.debug("Using generation options: %s", options)
            except Exception as e:
                logger.error("Failed to parse options: %s", e)
                raise ValueError(f"Invalid options: {e}")

        logger.info("Starting chat with model: %s", model)
        result = await ollama.chat(model, chat_messages, chat_tools, gen_options)
        logger.debug("Chat completed successfully")
        return format_response(result, format)
    except ModelNotFoundError:
        logger.error("Model not found: %s", model)
        raise
    except ValueError:
        raise
    except Exception as e:
        if "model not found" in str(e).lower():
            logger.error("Model not found: %s", model)
            raise ModelNotFoundError(model)
        logger.error("Chat handler error: %s", e, exc_info=True)
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
