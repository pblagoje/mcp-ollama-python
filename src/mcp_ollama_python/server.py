"""
MCP Server implementation for Ollama
"""

import json
from typing import Any, Dict, Optional
try:
    from mcp_ollama_python.ollama_client import OllamaClient
    from mcp_ollama_python.autoloader import discover_tools_with_handlers, ToolRegistry
    from mcp_ollama_python.models import ResponseFormat
except ImportError as e:
    from .ollama_client import OllamaClient
    from .autoloader import discover_tools_with_handlers, ToolRegistry
    from .models import ResponseFormat


class OllamaMCPServer:
    """MCP Server for Ollama operations"""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama_client = ollama_client or OllamaClient()
        self.tool_registry: Optional[ToolRegistry] = None
        self._resources: Dict[str, Dict[str, Any]] = {}
        self._prompts: Dict[str, Dict[str, Any]] = {}
        self._initialize_default_resources()
        self._initialize_default_prompts()

    async def handle_list_tools(self) -> Dict[str, Any]:
        """Handle list_tools request"""
        # Discover tools and cache the registry
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

    async def handle_call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Handle call_tool request"""
        try:
            # Ensure tool registry is loaded
            if self.tool_registry is None:
                self.tool_registry = await discover_tools_with_handlers()

            # Get the handler for this tool
            handler = self.tool_registry.get_handler(name)

            if not handler:
                raise ValueError(f"Unknown tool: {name}")

            # Determine format from args
            format_arg = args.get("format", "json")
            response_format = ResponseFormat.MARKDOWN if format_arg == "markdown" else ResponseFormat.JSON

            # Call the tool handler directly
            result = await handler(self.ollama_client, args, response_format)

            # Try to parse the result as JSON for structured content
            structured_data = None
            try:
                structured_data = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                pass

            return {
                "content": [
                    {
                        "type": "text",
                        "text": result,
                    }
                ],
                "structuredContent": structured_data,
            }

        except Exception as error:
            error_message = str(error) if isinstance(error, Exception) else str(error)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {error_message}",
                    }
                ],
                "isError": True,
            }

    def _initialize_default_resources(self):
        """Initialize default resources for the MCP server"""
        self._resources = {
            "ollama://models": {
                "uri": "ollama://models",
                "name": "Available Models",
                "description": "List of all available Ollama models",
                "mimeType": "application/json"
            },
            "ollama://running": {
                "uri": "ollama://running",
                "name": "Running Models",
                "description": "List of currently running models",
                "mimeType": "application/json"
            },
            "ollama://config": {
                "uri": "ollama://config",
                "name": "Ollama Configuration",
                "description": "Current Ollama server configuration",
                "mimeType": "application/json"
            }
        }

    def _initialize_default_prompts(self):
        """Initialize default prompts for the MCP server"""
        self._prompts = {
            "explain_lora": {
                "name": "explain_lora",
                "description": "Explain LoRA (Low-Rank Adaptation) technique",
                "arguments": [
                    {
                        "name": "detail_level",
                        "description": "Level of detail: basic, intermediate, or advanced",
                        "required": False
                    }
                ]
            },
            "code_review": {
                "name": "code_review",
                "description": "Review code and provide feedback",
                "arguments": [
                    {
                        "name": "language",
                        "description": "Programming language",
                        "required": True
                    },
                    {
                        "name": "focus",
                        "description": "Focus areas: security, performance, style, or all",
                        "required": False
                    }
                ]
            },
            "hello_world": {
                "name": "hello_world",
                "description": "Generate Hello World code in any language",
                "arguments": [
                    {
                        "name": "language",
                        "description": "Programming language",
                        "required": True
                    }
                ]
            }
        }

    async def handle_list_resources(self) -> Dict[str, Any]:
        """Handle list_resources request"""
        return {
            "resources": [
                {
                    "uri": resource["uri"],
                    "name": resource["name"],
                    "description": resource["description"],
                    "mimeType": resource.get("mimeType", "text/plain")
                }
                for resource in self._resources.values()
            ]
        }

    async def handle_read_resource(self, uri: str) -> Dict[str, Any]:
        """Handle read_resource request"""
        try:
            if uri not in self._resources:
                raise ValueError(f"Unknown resource: {uri}")

            # Fetch the actual resource data
            if uri == "ollama://models":
                data = await self.ollama_client.list()
                content = json.dumps(data, indent=2)
            elif uri == "ollama://running":
                data = await self.ollama_client.ps()
                content = json.dumps(data, indent=2)
            elif uri == "ollama://config":
                config_data = {
                    "host": self.ollama_client.host,
                    "has_api_key": bool(self.ollama_client.api_key)
                }
                content = json.dumps(config_data, indent=2)
            else:
                content = "Resource data not available"

            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": self._resources[uri].get("mimeType", "text/plain"),
                        "text": content
                    }
                ]
            }

        except Exception as error:
            error_message = str(error) if isinstance(error, Exception) else str(error)
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "text/plain",
                        "text": f"Error reading resource: {error_message}"
                    }
                ],
                "isError": True
            }

    async def handle_list_prompts(self) -> Dict[str, Any]:
        """Handle list_prompts request"""
        return {
            "prompts": [
                {
                    "name": prompt["name"],
                    "description": prompt["description"],
                    "arguments": prompt.get("arguments", [])
                }
                for prompt in self._prompts.values()
            ]
        }

    async def handle_get_prompt(self, name: str, arguments: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle get_prompt request"""
        try:
            if name not in self._prompts:
                raise ValueError(f"Unknown prompt: {name}")

            prompt_def = self._prompts[name]
            args = arguments or {}

            # Generate prompt based on name
            if name == "explain_lora":
                detail = args.get("detail_level", "basic")
                prompt_text = f"""Explain LoRA (Low-Rank Adaptation) at a {detail} level.
Include:
- What it is and why it's useful
- How it works technically
- Use cases and benefits
- Comparison with full fine-tuning"""
            elif name == "code_review":
                language = args.get("language", "Python")
                focus = args.get("focus", "all")
                prompt_text = f"""Review the following {language} code with focus on {focus}.
Provide:
- Issues found
- Suggestions for improvement
- Best practices recommendations
- Security concerns (if applicable)"""
            elif name == "hello_world":
                language = args.get("language", "Python")
                prompt_text = f"""Write a complete, well-commented Hello World program in {language}.
Include:
- Proper syntax and structure
- Comments explaining each part
- Best practices for the language
- How to run the program"""
            else:
                prompt_text = f"Prompt template for {name}"

            return {
                "description": prompt_def["description"],
                "messages": [
                    {
                        "role": "user",
                        "content": {
                            "type": "text",
                            "text": prompt_text
                        }
                    }
                ]
            }

        except Exception as error:
            error_message = str(error) if isinstance(error, Exception) else str(error)
            raise ValueError(f"Error getting prompt: {error_message}")
