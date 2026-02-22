"""
Ollama list models tool
"""

import logging
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def list_models_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    List all available Ollama models.

    Args:
        ollama: Ollama client instance
        args: Arguments (unused for this tool)
        format: Response format (JSON or Markdown)

    Returns:
        Formatted list of models with names, sizes, and modification dates
    """
    logger.debug("List models handler called")
    try:
        logger.info("Fetching list of models")
        result = await ollama.list()
        logger.debug("Successfully retrieved model list")
        return format_response(result, format)
    except Exception as e:
        logger.error("List models handler error: %s", e, exc_info=True)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_list",
    description="List all available Ollama models installed locally. Returns model names, sizes, and modification dates.",
    input_schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            }
        },
    },
)
