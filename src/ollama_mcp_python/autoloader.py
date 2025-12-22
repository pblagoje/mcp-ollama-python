"""
Tool autoloader - dynamically discovers and loads tools from the tools directory
"""

import importlib
import os
import pkgutil
from typing import List, Callable, Any, Dict, Tuple
from .models import ToolDefinition, ResponseFormat
from .ollama_client import OllamaClient


# Type for tool handler function
ToolHandler = Callable[[OllamaClient, Dict[str, Any], ResponseFormat], str]


class ToolRegistry:
    """Registry for tool definitions and their handlers"""
    def __init__(self):
        self.tools: List[ToolDefinition] = []
        self.handlers: Dict[str, ToolHandler] = {}
    
    def register(self, tool_def: ToolDefinition, handler: ToolHandler):
        """Register a tool definition with its handler"""
        self.tools.append(tool_def)
        self.handlers[tool_def.name] = handler
    
    def get_handler(self, tool_name: str) -> ToolHandler:
        """Get handler for a tool by name"""
        return self.handlers.get(tool_name)


async def discover_tools() -> List[ToolDefinition]:
    """Discover and load all tools from the tools directory (backward compatibility)"""
    registry = await discover_tools_with_handlers()
    return registry.tools


async def discover_tools_with_handlers() -> ToolRegistry:
    """Discover and load all tools with their handlers from the tools directory"""

    registry = ToolRegistry()

    # Get the tools package path
    tools_package = importlib.import_module('.tools', package='ollama_mcp_python')

    # Get the directory path
    if hasattr(tools_package, '__path__'):
        tools_dir = tools_package.__path__[0]
    else:
        # Fallback for different Python versions
        tools_dir = os.path.dirname(tools_package.__file__)

    # Iterate through all Python files in the tools directory
    for _, module_name, _ in pkgutil.iter_modules([tools_dir]):
        if module_name.startswith('__'):
            continue

        try:
            # Import the module
            module = importlib.import_module(f'.tools.{module_name}', package='ollama_mcp_python')

            # Check if module exports tool_definition
            if hasattr(module, 'tool_definition'):
                tool_def = getattr(module, 'tool_definition')
                
                # Convert dict to ToolDefinition if needed
                if isinstance(tool_def, dict):
                    tool_def = ToolDefinition(**tool_def)
                
                if isinstance(tool_def, ToolDefinition):
                    # Find the handler function (should end with _handler)
                    handler = None
                    for attr_name in dir(module):
                        if attr_name.endswith('_handler') and callable(getattr(module, attr_name)):
                            handler = getattr(module, attr_name)
                            break
                    
                    if handler:
                        registry.register(tool_def, handler)
                    else:
                        print(f"Warning: Tool {tool_def.name} has no handler function")

        except Exception as e:
            print(f"Warning: Failed to load tool {module_name}: {e}")
            continue

    return registry
