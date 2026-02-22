"""
Ollama execute tool - Direct code execution with AI assistance
"""

import logging
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any, List
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

logger = logging.getLogger(__name__)


async def execute_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Execute code directly or generate and execute using AI.

    Args:
        ollama: Ollama client instance
        args: Arguments containing code, language, generate flag, prompt, and model
        format: Response format (JSON or Markdown)

    Returns:
        Formatted execution results including stdout, stderr, and return code

    Raises:
        ValueError: If required arguments are missing
    """
    logger.debug("Execute handler called")
    code = args.get("code")
    language = args.get("language", "python")
    generate = args.get("generate", False)
    prompt = args.get("prompt")
    model = args.get("model", "llama3.1")

    # If generate is True, use AI to generate code first
    if generate and prompt:
        logger.info("Generating code using AI: model=%s, language=%s", model, language)
        try:
            gen_prompt = f"Write a complete, runnable {language} program that: {prompt}\n\nProvide only the code, no explanations."
            result = await ollama.generate(model, gen_prompt)
            code = result.get("response", "")
            logger.debug("Code generated successfully")

            # Clean up code (remove markdown code blocks if present)
            if "```" in code:
                lines = code.split("\n")
                code_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block:
                        code_lines.append(line)
                code = "\n".join(code_lines).strip()
        except Exception as e:
            logger.error("Failed to generate code: %s", e, exc_info=True)
            return format_response(
                {"error": f"Failed to generate code: {str(e)}"}, format
            )

    if not code:
        logger.error("Execute handler called without code")
        raise ValueError(
            "Code is required (either provided directly or generated via prompt)"
        )

    logger.info("Executing %s code", language)

    # Execute the code
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{_get_file_extension(language)}", delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        logger.debug("Created temporary file: %s", temp_file)

        try:
            # Get the command to run
            cmd = _get_execution_command(language, temp_file)
            logger.debug("Executing command: %s", cmd)

            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = {
                "code": code,
                "language": language,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }

            if generate:
                output["generated"] = True
                output["prompt"] = prompt

            logger.info("Execution completed: returncode=%d", result.returncode)
            return format_response(output, format)

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except OSError:
                pass

    except subprocess.TimeoutExpired:
        logger.warning("Execution timed out for %s code", language)
        return format_response(
            {"error": "Execution timed out (30 seconds limit)", "code": code}, format
        )
    except Exception as e:
        logger.error("Execution failed: %s", e, exc_info=True)
        return format_response(
            {"error": f"Execution failed: {str(e)}", "code": code}, format
        )


def _get_file_extension(language: str) -> str:
    """
    Get file extension for programming language.

    Args:
        language: Programming language name

    Returns:
        File extension for the language
    """
    extensions = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "java": "java",
        "c": "c",
        "cpp": "cpp",
        "go": "go",
        "rust": "rs",
        "ruby": "rb",
        "php": "php",
        "bash": "sh",
        "shell": "sh",
    }
    return extensions.get(language.lower(), "txt")


def _get_execution_command(language: str, file_path: str) -> List[str]:
    """
    Get execution command for programming language.

    Args:
        language: Programming language name
        file_path: Path to the code file

    Returns:
        Command list to execute the code

    Raises:
        ValueError: If language is not supported
    """
    commands = {
        "python": [sys.executable, file_path],
        "javascript": ["node", file_path],
        "typescript": ["ts-node", file_path],
        "bash": ["bash", file_path],
        "shell": ["sh", file_path],
        "ruby": ["ruby", file_path],
        "php": ["php", file_path],
        "go": ["go", "run", file_path],
    }

    cmd = commands.get(language.lower())
    if not cmd:
        raise ValueError(f"Unsupported language: {language}")

    return cmd


# Tool definition
tool_definition = ToolDefinition(
    name="ollama_execute",
    description="Execute code directly or generate and execute code using AI. Supports Python, JavaScript, and other languages.",
    input_schema={
        "type": "object",
        "properties": {
            "code": {
                "type": "string",
                "description": "Code to execute (required if generate=false)",
            },
            "language": {
                "type": "string",
                "description": "Programming language (default: python)",
                "enum": [
                    "python",
                    "javascript",
                    "typescript",
                    "bash",
                    "shell",
                    "ruby",
                    "php",
                    "go",
                ],
                "default": "python",
            },
            "generate": {
                "type": "boolean",
                "description": "Generate code using AI before executing (default: false)",
                "default": False,
            },
            "prompt": {
                "type": "string",
                "description": "Prompt for AI code generation (required if generate=true)",
            },
            "model": {
                "type": "string",
                "description": "Model to use for code generation (default: llama3.1)",
                "default": "llama3.1",
            },
            "format": {
                "type": "string",
                "enum": ["json", "markdown"],
                "description": "Output format (default: json)",
                "default": "json",
            },
        },
        "required": [],
    },
)
