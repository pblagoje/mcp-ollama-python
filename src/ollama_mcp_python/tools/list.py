"""
Ollama list models tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def list_models_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """List all available Ollama models"""
    result = await ollama.list()
    return format_response(result, format)


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
