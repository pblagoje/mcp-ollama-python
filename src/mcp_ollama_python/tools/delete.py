"""
Ollama delete model tool
"""

import logging
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def delete_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Remove models from local Ollama storage.

    Args:
        ollama: Ollama client instance
        args: Arguments containing model name
        format: Response format (JSON or Markdown)

    Returns:
        Formatted deletion status

    Raises:
        ValueError: If model name is missing
        ModelNotFoundError: If the specified model is not found
    """
    model = args.get("model")
    if not model:
        logger.error("Delete handler called without model name")
        raise ValueError("Model name is required")

    logger.debug("Delete handler called for model: %s", model)

    try:
        logger.info("Deleting model: %s", model)
        result = await ollama.delete(model)
        logger.info("Successfully deleted model: %s", model)
        return format_response(result, format)
    except ModelNotFoundError:
        logger.error("Model not found: %s", model)
        raise
    except Exception as e:
        if "model not found" in str(e).lower() or "no such file" in str(e).lower():
            logger.error("Model not found: %s", model)
            raise ModelNotFoundError(model)
        logger.error("Delete handler error for model %s: %s", model, e, exc_info=True)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_delete",
    description="Remove models from local Ollama storage to free up disk space.",
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Name of the model to delete",
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
