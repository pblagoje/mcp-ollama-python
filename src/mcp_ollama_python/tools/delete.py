"""
Ollama delete model tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def delete_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Remove models from local storage"""
    model = args.get("model")
    if not model:
        raise ValueError("Model name is required")

    try:
        result = await ollama.delete(model)
        return format_response(result, format)
    except Exception as e:
        if "model not found" in str(e).lower() or "no such file" in str(e).lower():
            raise ModelNotFoundError(model)
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
