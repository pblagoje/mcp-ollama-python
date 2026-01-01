"""
Ollama generate text tool
"""

from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat, GenerationOptions, ModelNotFoundError
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def generate_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Generate text completions"""
    model = args.get("model")
    prompt = args.get("prompt")
    options = args.get("options")

    if not model:
        raise ValueError("Model name is required")
    if not prompt:
        raise ValueError("Prompt is required")

    try:
        gen_options = GenerationOptions(**options) if options else None
        result = await ollama.generate(model, prompt, gen_options)
        return format_response(result, format)
    except Exception as e:
        if "model not found" in str(e).lower():
            raise ModelNotFoundError(model)
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
