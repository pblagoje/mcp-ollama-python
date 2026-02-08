"""
Ollama embed tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def embed_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Generate embeddings for text"""
    model = args.get("model")
    input_text = args.get("input")

    if not model:
        raise ValueError("Model name is required")
    if not input_text:
        raise ValueError("Input text is required")

    try:
        result = await ollama.embed(model, input_text)
        return format_response(result, format)
    except Exception as e:
        if "model not found" in str(e).lower():
            raise ModelNotFoundError(model)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_embed",
    description="Generate vector embeddings for text using Ollama's embedding models like nomic-embed-text.",
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Name of the embedding model (e.g., 'nomic-embed-text')",
            },
            "input": {
                "oneOf": [
                    {"type": "string", "description": "Single text string to embed"},
                    {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of text strings to embed",
                    },
                ],
                "description": "Text or array of texts to generate embeddings for",
            },
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            },
        },
        "required": ["model", "input"],
    },
)
