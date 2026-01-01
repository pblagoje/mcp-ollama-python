"""
Ollama execute tool - Direct code execution with AI assistance
"""

import subprocess
import tempfile
import os
import sys
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response


async def execute_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Execute code with optional AI generation"""
    code = args.get("code")
    language = args.get("language", "python")
    generate = args.get("generate", False)
    prompt = args.get("prompt")
    model = args.get("model", "llama3.1")

    # If generate is True, use AI to generate code first
    if generate and prompt:
        try:
            gen_prompt = f"Write a complete, runnable {language} program that: {prompt}\n\nProvide only the code, no explanations."
            result = await ollama.generate(model, gen_prompt)
            code = result.get("response", "")
            
            # Clean up code (remove markdown code blocks if present)
            if "```" in code:
                lines = code.split("\n")
                code_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or (not any(line.strip().startswith(x) for x in ["```"])):
                        code_lines.append(line)
                code = "\n".join(code_lines).strip()
        except Exception as e:
            return format_response({
                "error": f"Failed to generate code: {str(e)}"
            }, format)

    if not code:
        raise ValueError("Code is required (either provided directly or generated via prompt)")

    # Execute the code
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix=f'.{_get_file_extension(language)}',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Get the command to run
            cmd = _get_execution_command(language, temp_file)
            
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                shell=True if sys.platform == "win32" else False
            )

            output = {
                "code": code,
                "language": language,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "success": result.returncode == 0
            }

            if generate:
                output["generated"] = True
                output["prompt"] = prompt

            return format_response(output, format)

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except:
                pass

    except subprocess.TimeoutExpired:
        return format_response({
            "error": "Execution timed out (30 seconds limit)",
            "code": code
        }, format)
    except Exception as e:
        return format_response({
            "error": f"Execution failed: {str(e)}",
            "code": code
        }, format)


def _get_file_extension(language: str) -> str:
    """Get file extension for language"""
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
        "shell": "sh"
    }
    return extensions.get(language.lower(), "txt")


def _get_execution_command(language: str, file_path: str) -> list:
    """Get execution command for language"""
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
                "enum": ["python", "javascript", "typescript", "bash", "shell", "ruby", "php", "go"],
                "default": "python"
            },
            "generate": {
                "type": "boolean",
                "description": "Generate code using AI before executing (default: false)",
                "default": False
            },
            "prompt": {
                "type": "string",
                "description": "Prompt for AI code generation (required if generate=true)",
            },
            "model": {
                "type": "string",
                "description": "Model to use for code generation (default: llama3.1)",
                "default": "llama3.1"
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
