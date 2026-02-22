"""
Ollama generate text tool
"""

import logging
from typing import Dict, Any, Optional
from ..models import (
    ToolDefinition,
    ResponseFormat,
    GenerationOptions,
    ModelNotFoundError,
)
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def generate_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Generate text completions using Ollama models.

    Args:
        ollama: Ollama client instance
        args: Arguments containing model, prompt, and options
        format: Response format (JSON or Markdown)

    Returns:
        Formatted generation response as string

    Raises:
        ValueError: If required arguments are missing
        ModelNotFoundError: If the specified model is not found
    """
    model = args.get("model")
    prompt = args.get("prompt")
    options = args.get("options")

    if not model:
        logger.error("Generate handler called without model name")
        raise ValueError("Model name is required")
    if not prompt:
        logger.error("Generate handler called without prompt")
        raise ValueError("Prompt is required")

    logger.debug("Generate handler called with model: %s", model)

    try:
        gen_options: Optional[GenerationOptions] = None
        if options:
            try:
                gen_options = GenerationOptions(**options)
                logger.debug("Using generation options: %s", options)
            except Exception as e:
                logger.error("Failed to parse options: %s", e)
                raise ValueError(f"Invalid options: {e}")

        logger.info("Starting generation with model: %s", model)
        result = await ollama.generate(model, prompt, gen_options)
        logger.debug("Generation completed successfully")
        return format_response(result, format)
    except ModelNotFoundError:
        logger.error("Model not found: %s", model)
        raise
    except ValueError:
        raise
    except Exception as e:
        if "model not found" in str(e).lower():
            logger.error("Model not found: %s", model)
            raise ModelNotFoundError(model)
        logger.error("Generate handler error: %s", e, exc_info=True)
        raise


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_generate",
    description="Generate text completions using Ollama models with configurable parameters.",
    input_schema={
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "description": "Name of the model to use for generation",
            },
            "prompt": {
                "type": "string",
                "description": "The prompt to generate text from",
            },
            "options": {
                "type": "object",
                "description": "Generation options (temperature, top_p, etc.)",
                "properties": {
                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                    "top_p": {"type": "number", "minimum": 0, "maximum": 1},
                    "top_k": {"type": "integer", "minimum": 0},
                    "num_predict": {"type": "integer", "minimum": 1},
                    "repeat_penalty": {"type": "number", "minimum": 0},
                    "seed": {"type": "integer"},
                    "stop": {"type": "array", "items": {"type": "string"}},
                },
            },
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            },
        },
        "required": ["model", "prompt"],
    },
)
