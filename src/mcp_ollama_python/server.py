"""
MCP Server implementation for Ollama
"""

import json
import logging
from typing import Any, Dict, Optional, List
from dataclasses import dataclass

try:
    from mcp_ollama_python.ollama_client import OllamaClient
    from mcp_ollama_python.autoloader import discover_tools_with_handlers, ToolRegistry
    from mcp_ollama_python.models import ResponseFormat
except ImportError:
    from .ollama_client import OllamaClient
    from .autoloader import discover_tools_with_handlers, ToolRegistry
    from .models import ResponseFormat

# Configure logging
logger = logging.getLogger(__name__)

# Constants
RESOURCE_URI_MODELS = "ollama://models"
RESOURCE_URI_RUNNING = "ollama://running"
RESOURCE_URI_CONFIG = "ollama://config"

MIME_TYPE_JSON = "application/json"
MIME_TYPE_TEXT = "text/plain"

PROMPT_EXPLAIN_LORA = "explain_lora"
PROMPT_CODE_REVIEW = "code_review"
PROMPT_HELLO_WORLD = "hello_world"
PROMPT_EXPLAIN_CODE = "explain_code"
PROMPT_WRITE_DOCSTRING = "write_docstring"


@dataclass
class ResourceDefinition:
    """Definition of a resource for the MCP server"""

    uri: str
    name: str
    description: str
    mime_type: str = MIME_TYPE_TEXT


@dataclass
class PromptDefinition:
    """Definition of a prompt for the MCP server"""

    name: str
    description: str
    arguments: List[Dict[str, Any]]


class OllamaMCPServer:
    """MCP Server for Ollama operations"""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama_client = ollama_client or OllamaClient()
        self.tool_registry: Optional[ToolRegistry] = None
        self._resources: Dict[str, ResourceDefinition] = {}
        self._prompts: Dict[str, PromptDefinition] = {}
        self._initialize_default_resources()
        self._initialize_default_prompts()

    async def handle_list_tools(self) -> Dict[str, Any]:
        """Handle list_tools request"""
        try:
            # Discover tools and cache the registry (only once)
            if self.tool_registry is None:
                self.tool_registry = await discover_tools_with_handlers()

            return {
                "tools": [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.input_schema,
                    }
                    for tool in self.tool_registry.tools
                ]
            }
        except Exception as error:
            logger.error("Error in handle_list_tools: %s", error)
            return {"tools": []}

    async def handle_call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call_tool request"""
        # Validate input
        if not isinstance(name, str) or not name.strip():
            return self._create_error_response("Invalid tool name")

        if not isinstance(args, dict):
            return self._create_error_response("Invalid tool arguments")

        try:
            # Ensure tool registry is loaded (only once)
            if self.tool_registry is None:
                self.tool_registry = await discover_tools_with_handlers()

            # Get the handler for this tool
            handler = self.tool_registry.get_handler(name)

            if not handler:
                return self._create_error_response(f"Unknown tool: {name}")

            # Determine format from args
            format_arg = args.get("format", "json")
            response_format = (
                ResponseFormat.MARKDOWN
                if format_arg == "markdown"
                else ResponseFormat.JSON
            )

            # Call the tool handler directly
            result = await handler(self.ollama_client, args, response_format)

            # Safely parse the result as JSON for structured content
            structured_data = None
            if isinstance(result, str) and result.strip():
                try:
                    structured_data = json.loads(result)
                except (json.JSONDecodeError, TypeError):
                    logger.debug("Failed to parse structured data from tool %s", name)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": result if isinstance(result, str) else str(result),
                    }
                ],
                "structuredContent": structured_data,
            }

        except Exception as error:
            logger.error("Error in handle_call_tool for %s: %s", name, error)
            return self._create_error_response(str(error))

    def _create_error_response(self, message: str) -> Dict[str, Any]:
        """Create a standardized error response"""
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {message}",
                }
            ],
            "isError": True,
        }

    def _initialize_default_resources(self):
        """Initialize default resources for the MCP server"""
        self._resources = {
            RESOURCE_URI_MODELS: ResourceDefinition(
                uri=RESOURCE_URI_MODELS,
                name="Available Models",
                description="List of all available Ollama models",
                mime_type=MIME_TYPE_JSON,
            ),
            RESOURCE_URI_RUNNING: ResourceDefinition(
                uri=RESOURCE_URI_RUNNING,
                name="Running Models",
                description="List of currently running models",
                mime_type=MIME_TYPE_JSON,
            ),
            RESOURCE_URI_CONFIG: ResourceDefinition(
                uri=RESOURCE_URI_CONFIG,
                name="Ollama Configuration",
                description="Current Ollama server configuration",
                mime_type=MIME_TYPE_JSON,
            ),
        }

    def _initialize_default_prompts(self):
        """Initialize default prompts for the MCP server"""
        self._prompts = {
            PROMPT_EXPLAIN_LORA: PromptDefinition(
                name=PROMPT_EXPLAIN_LORA,
                description="Explain LoRA (Low-Rank Adaptation) technique",
                arguments=[
                    {
                        "name": "detail_level",
                        "description": "Level of detail: basic, intermediate, or advanced",
                        "required": False,
                    }
                ],
            ),
            PROMPT_CODE_REVIEW: PromptDefinition(
                name=PROMPT_CODE_REVIEW,
                description="Review code and provide feedback",
                arguments=[
                    {
                        "name": "language",
                        "description": "Programming language",
                        "required": True,
                    },
                ],
            ),
            PROMPT_HELLO_WORLD: PromptDefinition(
                name=PROMPT_HELLO_WORLD,
                description="Generate Hello World code in any language",
                arguments=[
                    {
                        "name": "language",
                        "description": "Programming language",
                        "required": True,
                    }
                ],
            ),
            PROMPT_EXPLAIN_CODE: PromptDefinition(
                name=PROMPT_EXPLAIN_CODE,
                description="Explain what a code snippet does in detail",
                arguments=[
                    {
                        "name": "code",
                        "description": "The code snippet to explain",
                        "required": True,
                    },
                    {
                        "name": "language",
                        "description": "Programming language of the code",
                        "required": False,
                    },
                ],
            ),
            PROMPT_WRITE_DOCSTRING: PromptDefinition(
                name=PROMPT_WRITE_DOCSTRING,
                description="Generate comprehensive docstring/documentation for code",
                arguments=[
                    {
                        "name": "code",
                        "description": "The code to document",
                        "required": True,
                    },
                    {
                        "name": "language",
                        "description": "Programming language (e.g., python, javascript, typescript)",
                        "required": True,
                    },
                    {
                        "name": "style",
                        "description": "Documentation style (e.g., google, numpy, jsdoc, sphinx)",
                        "required": False,
                    },
                ],
            ),
        }

    async def handle_list_resources(self) -> Dict[str, Any]:
        """Handle list_resources request"""
        try:
            return {
                "resources": [
                    {
                        "uri": resource.uri,
                        "name": resource.name,
                        "description": resource.description,
                        "mimeType": resource.mime_type,
                    }
                    for resource in self._resources.values()
                ]
            }
        except Exception as error:
            logger.error("Error in handle_list_resources: %s", error)
            return {"resources": []}

    async def handle_read_resource(self, uri: str) -> Dict[str, Any]:
        """Handle read_resource request"""
        # Handle both old and new MCP SDK formats
        # MCP SDK v1.26.0 might send uri as a dict with 'uri' key
        actual_uri = uri
        if isinstance(uri, dict):
            actual_uri = uri.get("uri", "")
        elif not isinstance(uri, str):
            actual_uri = str(uri) if uri else ""

        # Validate input
        if not isinstance(actual_uri, str) or not actual_uri.strip():
            return {
                "contents": [
                    {
                        "uri": actual_uri if isinstance(actual_uri, str) else str(uri),
                        "mimeType": MIME_TYPE_TEXT,
                        "text": "Error reading resource: Invalid URI",
                    }
                ],
                "isError": True,
            }

        # Use actual_uri for the rest of the function
        uri = actual_uri

        try:
            if uri not in self._resources:
                raise ValueError(f"Unknown resource: {uri}")

            resource = self._resources[uri]

            # Fetch the actual resource data
            if uri == RESOURCE_URI_MODELS:
                data = await self.ollama_client.list()
                content = json.dumps(data, indent=2)
            elif uri == RESOURCE_URI_RUNNING:
                data = await self.ollama_client.ps()
                content = json.dumps(data, indent=2)
            elif uri == RESOURCE_URI_CONFIG:
                config_data = {
                    "host": self.ollama_client.host,
                    "has_api_key": bool(self.ollama_client.api_key),
                }
                content = json.dumps(config_data, indent=2)
            else:
                content = "Resource data not available"

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": resource.mime_type,
                        "text": content,
                    }
                ]
            }

        except Exception as error:
            logger.error("Error in handle_read_resource for %s: %s", uri, error)
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": MIME_TYPE_TEXT,
                        "text": f"Error reading resource: {str(error)}",
                    }
                ],
                "isError": True,
            }

    async def handle_list_prompts(self) -> Dict[str, Any]:
        """Handle list_prompts request"""
        try:
            return {
                "prompts": [
                    {
                        "name": prompt.name,
                        "description": prompt.description,
                        "arguments": prompt.arguments,
                    }
                    for prompt in self._prompts.values()
                ]
            }
        except Exception as error:
            logger.error("Error in handle_list_prompts: %s", error)
            return {"prompts": []}

    async def handle_get_prompt(
        self, name: str, arguments: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Handle get_prompt request"""
        # Validate input
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Invalid prompt name")

        try:
            if name not in self._prompts:
                raise ValueError(f"Unknown prompt: {name}")

            prompt_def = self._prompts[name]
            args = arguments or {}

            # Generate prompt based on name
            if name == PROMPT_EXPLAIN_LORA:
                detail = args.get("detail_level", "basic")
                prompt_text = f"""Explain LoRA (Low-Rank Adaptation) at a {detail} level.
Include:
- What it is and why it's useful
- How it works technically
- Use cases and benefits
- Comparison with full fine-tuning"""
            elif name == PROMPT_CODE_REVIEW:
                language = args.get("language", "Python")
                prompt_text = f"""Review the following {language} code with focus on identifying potential bugs and correctness issues.
You are a senior software engineer performing a deep code review. Your analysis should emphasize:

1. Logic flaws or incorrect behavior
2. Missing or unhandled edge cases
3. Null/undefined reference risks
4. Concurrency or race‑condition vulnerabilities
5. Security weaknesses
6. Resource‑management issues or leaks
7. Violations of API contracts
8. Incorrect or ineffective caching behavior (staleness, key bugs, invalidation issues)
9. Inconsistencies with established patterns or conventions

Additional requirements:
- When exploring the codebase, use multiple tools in parallel for efficiency, but avoid excessive exploration.
- Report any pre‑existing bugs you discover, not just those introduced by the changes.
- Do not include speculative or low‑confidence findings; base conclusions on a solid understanding of the code.
- Be aware that the referenced commit may not reflect the current local checkout state."""
            elif name == PROMPT_HELLO_WORLD:
                language = args.get("language", "Python")
                prompt_text = f"""Write a complete, well-commented Hello World program in {language}.
Include:
- Proper syntax and structure
- Comments explaining each part
- Best practices for the language
- How to run the program"""
            elif name == PROMPT_EXPLAIN_CODE:
                code = args.get("code", "")
                if not code:
                    raise ValueError(
                        "The 'code' parameter is required for explain_code prompt"
                    )
                language = args.get("language", "")
                lang_hint = f" ({language})" if language else ""
                prompt_text = f"""Explain the following code{lang_hint} in detail:

```
{code}
```

Provide a comprehensive explanation that includes:
1. **Overview**: What does this code do at a high level?
2. **Step-by-step breakdown**: Explain each significant part
3. **Key concepts**: What programming concepts or patterns are used?
4. **Inputs and outputs**: What does it expect and what does it produce?
5. **Potential issues**: Any edge cases, bugs, or improvements to consider?

Be clear and educational in your explanation."""
            elif name == PROMPT_WRITE_DOCSTRING:
                code = args.get("code", "")
                if not code:
                    raise ValueError(
                        "The 'code' parameter is required for write_docstring prompt"
                    )
                language = args.get("language", "python")
                style = args.get("style", "")
                style_hint = f" in {style} style" if style else ""
                prompt_text = f"""Generate comprehensive documentation{style_hint} for the following {language} code:

```{language}
{code}
```

Requirements:
1. Write proper docstring/documentation comments appropriate for {language}
2. Include:
   - Brief description of what the code does
   - Parameters/arguments with types and descriptions
   - Return value with type and description
   - Exceptions/errors that may be raised
   - Usage examples if applicable
   - Any important notes or warnings
3. Follow {language} documentation conventions{style_hint}
4. Be clear, concise, and complete

Provide ONLY the documentation/docstring, formatted correctly for insertion into the code."""
            else:
                prompt_text = f"Prompt template for {name}"

            return {
                "description": prompt_def.description,
                "messages": [
                    {"role": "user", "content": {"type": "text", "text": prompt_text}}
                ],
            }

        except Exception as error:
            logger.error("Error in handle_get_prompt for %s: %s", name, error)
            raise ValueError(f"Error getting prompt: {str(error)}")
