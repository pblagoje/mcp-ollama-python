"""
Ollama pull model tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def pull_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Download models from Ollama library"""
    model = args.get("model")
    if not model:
        raise ValueError("Model name is required")

    result = await ollama.pull(model)
    return format_response(result, format)


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
