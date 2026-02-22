"""
Ollama pull model tool
"""

import logging
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def pull_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Download and install models from the Ollama library.

    Args:
        ollama: Ollama client instance
        args: Arguments containing model name
        format: Response format (JSON or Markdown)

    Returns:
        Formatted pull operation status

    Raises:
        ValueError: If model name is missing
    """
    model = args.get("model")
    if not model:
        logger.error("Pull handler called without model name")
        raise ValueError("Model name is required")

    logger.debug("Pull handler called for model: %s", model)

    try:
        logger.info("Starting pull for model: %s", model)
        result = await ollama.pull(model)
        logger.info("Successfully pulled model: %s", model)
        return format_response(result, format)
    except Exception as e:
        logger.error("Pull handler error for model %s: %s", model, e, exc_info=True)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_pull",
    description="Download and install models from the Ollama library to your local machine.",
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Name of the model to pull (e.g., 'llama3.2', 'mistral', 'codellama')",
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
