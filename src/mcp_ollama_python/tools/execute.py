"""
Ollama execute tool - Direct code execution with AI assistance

Disabled by default. Set OLLAMA_EXECUTE_ENABLED=1 to expose this tool.
"""

import logging
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List

from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response
from ..security import (
    MAX_EXECUTE_PROMPT_LEN,
    is_execute_enabled,
    validate_code_payload,
    validate_model_name,
)

logger = logging.getLogger(__name__)

_EXECUTE_TIMEOUT_SECONDS = 30
_ALLOWED_LANGUAGES = frozenset(
    {"python", "javascript", "typescript", "ruby", "php", "go"}
)


def _execution_disabled_message() -> str:
    return (
        "ollama_execute is disabled. Set OLLAMA_EXECUTE_ENABLED=1 in the "
        "environment to enable local code execution (use only on trusted machines)."
    )


async def execute_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """
    Execute code directly or generate and execute using AI.

    Requires OLLAMA_EXECUTE_ENABLED=1. Shell/bash execution is not supported.
    """
    if not is_execute_enabled():
        logger.warning("ollama_execute called while disabled")
        return format_response({"error": _execution_disabled_message()}, format)

    logger.debug("Execute handler called")
    code = args.get("code")
    language = str(args.get("language", "python")).lower()
    generate = args.get("generate", False)
    prompt = args.get("prompt")
    model = args.get("model", "llama3.1")

    if language not in _ALLOWED_LANGUAGES:
        raise ValueError(
            f"Unsupported language: {language}. "
            f"Allowed: {', '.join(sorted(_ALLOWED_LANGUAGES))}"
        )

    validate_model_name(model)

    if generate and prompt:
        if len(str(prompt)) > MAX_EXECUTE_PROMPT_LEN:
            raise ValueError(
                f"Prompt exceeds maximum length of {MAX_EXECUTE_PROMPT_LEN} characters"
            )
        logger.info("Generating code using AI: model=%s, language=%s", model, language)
        try:
            gen_prompt = (
                f"Write a complete, runnable {language} program that: {prompt}\n\n"
                "Provide only the code, no explanations."
            )
            result = await ollama.generate(model, gen_prompt)
            code = result.get("response", "")
            logger.debug("Code generated successfully")

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

    code = validate_code_payload(str(code))
    logger.info("Executing %s code", language)

    try:
        with tempfile.TemporaryDirectory(prefix="mcp_ollama_exec_") as workdir:
            suffix = f".{_get_file_extension(language)}"
            temp_file = os.path.join(workdir, f"snippet{suffix}")
            with open(temp_file, "w", encoding="utf-8") as handle:
                handle.write(code)

            cmd = _get_execution_command(language, temp_file)
            logger.debug("Executing command: %s", cmd)

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=_EXECUTE_TIMEOUT_SECONDS,
                cwd=workdir,
                env=_minimal_subprocess_env(),
            )

            output = {
                "language": language,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0,
            }

            if generate:
                output["generated"] = True

            logger.info("Execution completed: returncode=%d", result.returncode)
            return format_response(output, format)

    except subprocess.TimeoutExpired:
        logger.warning("Execution timed out for %s code", language)
        return format_response(
            {
                "error": f"Execution timed out ({_EXECUTE_TIMEOUT_SECONDS} seconds limit)",
            },
            format,
        )
    except Exception as e:
        logger.error("Execution failed: %s", e, exc_info=True)
        return format_response({"error": f"Execution failed: {str(e)}"}, format)


def _minimal_subprocess_env() -> Dict[str, str]:
    """Return a reduced environment for untrusted code execution."""
    keep = (
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "HOME",
        "USERPROFILE",
        "TEMP",
        "TMP",
        "LANG",
        "LC_ALL",
        "PYTHONIOENCODING",
    )
    return {key: value for key, value in os.environ.items() if key in keep and value}


def _get_file_extension(language: str) -> str:
    extensions = {
        "python": "py",
        "javascript": "js",
        "typescript": "ts",
        "go": "go",
        "ruby": "rb",
        "php": "php",
    }
    return extensions.get(language.lower(), "txt")


def _get_execution_command(language: str, file_path: str) -> List[str]:
    commands = {
        "python": [sys.executable, file_path],
        "javascript": ["node", file_path],
        "typescript": ["ts-node", file_path],
        "ruby": ["ruby", file_path],
        "php": ["php", file_path],
        "go": ["go", "run", file_path],
    }

    cmd = commands.get(language.lower())
    if not cmd:
        raise ValueError(f"Unsupported language: {language}")

    return cmd


# Tool definition — only registered when OLLAMA_EXECUTE_ENABLED=1 (see autoloader)
tool_definition = ToolDefinition(
    name="ollama_execute",
    description=(
        "Execute code locally (opt-in: set OLLAMA_EXECUTE_ENABLED=1). "
        "Supports Python, JavaScript, TypeScript, Ruby, PHP, and Go. "
        "Shell/bash is not supported."
    ),
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
                "enum": sorted(_ALLOWED_LANGUAGES),
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
