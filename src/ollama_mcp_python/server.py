"""
MCP Server implementation for Ollama
"""

import asyncio
import os
from typing import Any, Dict, Optional
from .ollama_client import OllamaClient
from .autoloader import discover_tools_with_handlers, ToolRegistry
from .models import ResponseFormat, ToolDefinition
from .response_formatter import format_response


class OllamaMCPServer:
    """MCP Server for Ollama operations"""

    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        self.ollama_client = ollama_client or OllamaClient()
        self.tool_registry: Optional[ToolRegistry] = None

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
            format = ResponseFormat.MARKDOWN if format_arg == "markdown" else ResponseFormat.JSON

            # Call the tool handler directly
            result = await handler(self.ollama_client, args, format)

            # Try to parse the result as JSON for structured content
            structured_data = None
            try:
                import json
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

