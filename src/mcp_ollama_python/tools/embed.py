"""
Ollama embed tool
"""

import logging
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def embed_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Generate vector embeddings for text using Ollama embedding models.

    Args:
        ollama: Ollama client instance
        args: Arguments containing model and input text
        format: Response format (JSON or Markdown)

    Returns:
        Formatted embeddings response

    Raises:
        ValueError: If required arguments are missing
        ModelNotFoundError: If the specified model is not found
    """
    model = args.get("model")
    input_text = args.get("input")

    if not model:
        logger.error("Embed handler called without model name")
        raise ValueError("Model name is required")
    if not input_text:
        logger.error("Embed handler called without input text")
        raise ValueError("Input text is required")

    logger.debug("Embed handler called with model: %s", model)

    try:
        logger.info("Generating embeddings with model: %s", model)
        result = await ollama.embed(model, input_text)
        logger.debug("Embeddings generated successfully")
        return format_response(result, format)
    except ModelNotFoundError:
        logger.error("Model not found: %s", model)
        raise
    except Exception as e:
        if "model not found" in str(e).lower():
            logger.error("Model not found: %s", model)
            raise ModelNotFoundError(model)
        logger.error("Embed handler error: %s", e, exc_info=True)
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
