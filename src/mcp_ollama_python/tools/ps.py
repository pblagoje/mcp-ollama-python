"""
Ollama ps (running models) tool
"""

import logging
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def ps_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    List currently running/loaded Ollama models.

    Args:
        ollama: Ollama client instance
        args: Arguments (unused for this tool)
        format: Response format (JSON or Markdown)

    Returns:
        Formatted list of running models with memory usage and runtime info
    """
    logger.debug("PS handler called")
    try:
        logger.info("Fetching running models")
        result = await ollama.ps()
        logger.debug("Successfully retrieved running models")
        return format_response(result, format)
    except Exception as e:
        logger.error("PS handler error: %s", e, exc_info=True)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_ps",
    description="List all currently running/loaded models in Ollama, showing memory usage and runtime information.",
    input_schema={
        "type": "object",
        "properties": {
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            },
        },
    },
)
