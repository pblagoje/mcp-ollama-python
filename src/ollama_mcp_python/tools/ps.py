"""
Ollama ps (running models) tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def ps_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """List currently running models"""
    result = await ollama.ps()
    return format_response(result, format)


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
