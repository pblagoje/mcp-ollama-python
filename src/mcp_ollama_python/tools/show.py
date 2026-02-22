"""
Ollama show model tool
"""

import logging
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def show_model_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Show detailed information about a specific Ollama model.

    Args:
        ollama: Ollama client instance
        args: Arguments containing model name
        format: Response format (JSON or Markdown)

    Returns:
        Formatted model information including size, parameters, and capabilities

    Raises:
        ValueError: If model name is missing
        ModelNotFoundError: If the specified model is not found
    """
    model = args.get("model")
    if not model:
        logger.error("Show model handler called without model name")
        raise ValueError("Model name is required")

    logger.debug("Show model handler called for model: %s", model)

    try:
        logger.info("Fetching information for model: %s", model)
        result = await ollama.show(model)
        logger.debug("Successfully retrieved model information")
        return format_response(result, format)
    except ModelNotFoundError:
        logger.error("Model not found: %s", model)
        raise
    except Exception as e:
        if "model not found" in str(e).lower():
            logger.error("Model not found: %s", model)
            raise ModelNotFoundError(model)
        logger.error("Show model handler error: %s", e, exc_info=True)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_show",
    description="Get detailed information about a specific Ollama model including size, parameters, and capabilities.",
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Name of the model to show information for",
            },
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            },
        },
        "required": ["model"],
    },
)
