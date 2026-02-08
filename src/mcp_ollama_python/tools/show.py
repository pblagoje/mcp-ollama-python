"""
Ollama show model tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def show_model_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Show detailed information about a specific model"""
    model = args.get("model")
    if not model:
        raise ValueError("Model name is required")

    try:
        result = await ollama.show(model)
        return format_response(result, format)
    except Exception as e:
        if "model not found" in str(e).lower():
            raise ModelNotFoundError(model)
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
