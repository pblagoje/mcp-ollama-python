"""
Tool autoloader - dynamically discovers and loads tools from the tools directory
"""

import importlib
import logging
import os
import pkgutil
from typing import List, Callable, Any, Dict, Optional

try:
    from mcp_ollama_python.ollama_client import OllamaClient
    from mcp_ollama_python.models import ToolDefinition, ResponseFormat
except ImportError:
    from .ollama_client import OllamaClient
    from .models import ToolDefinition, ResponseFormat

# Configure logging
logger = logging.getLogger(__name__)

# Type for tool handler function
ToolHandler = Callable[[OllamaClient, Dict[str, Any], ResponseFormat], str]


class ToolRegistry:
    """
    Registry for tool definitions and their handlers.

    Maintains a collection of tools and their associated handler functions,
    allowing dynamic tool discovery and execution.
    """

    def __init__(self):
        self.tools: List[ToolDefinition] = []
        self.handlers: Dict[str, ToolHandler] = {}
        logger.debug("ToolRegistry initialized")

    def register(self, tool_def: ToolDefinition, handler: ToolHandler) -> None:
        """
        Register a tool definition with its handler.

        Args:
            tool_def: Tool definition containing metadata
            handler: Async function that handles tool execution
        """
        if not isinstance(tool_def, ToolDefinition):
            raise TypeError("tool_def must be a ToolDefinition instance")
        if not callable(handler):
            raise TypeError("handler must be callable")

        self.tools.append(tool_def)
        self.handlers[tool_def.name] = handler
        logger.debug("Registered tool: %s", tool_def.name)

    def get_handler(self, tool_name: str) -> Optional[ToolHandler]:
        """
        Get handler for a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool handler function or None if not found
        """
        handler = self.handlers.get(tool_name)
        if handler:
            logger.debug("Found handler for tool: %s", tool_name)
        else:
            logger.warning("No handler found for tool: %s", tool_name)
        return handler


async def discover_tools() -> List[ToolDefinition]:
    """
    Discover and load all tools from the tools directory.

    This function is maintained for backward compatibility.
    Use discover_tools_with_handlers() for new code.

    Returns:
        List of discovered tool definitions
    """
    logger.debug("Discovering tools (backward compatibility mode)")
    registry = await discover_tools_with_handlers()
    logger.info("Discovered %d tools", len(registry.tools))
    return registry.tools


async def discover_tools_with_handlers() -> ToolRegistry:
    """
    Discover and load all tools with their handlers from the tools directory.

    Scans the tools package for modules containing tool definitions and their
    associated handler functions. Each tool module should export:
    - tool_definition: ToolDefinition or dict with tool metadata
    - *_handler: Async function that handles tool execution

    Returns:
        ToolRegistry containing all discovered tools and handlers

    Raises:
        ImportError: If tools package cannot be imported
    """
    logger.info("Starting tool discovery")
    registry = ToolRegistry()

    try:
        # Get the tools package path
        tools_package = importlib.import_module(".tools", package="mcp_ollama_python")
        logger.debug("Tools package imported successfully")
    except ImportError as e:
        logger.error("Failed to import tools package: %s", e)
        raise

    # Get the directory path
    if hasattr(tools_package, "__path__"):
        tools_dir = tools_package.__path__[0]
    else:
        # Fallback for different Python versions
        tools_dir = os.path.dirname(tools_package.__file__)

    logger.debug("Tools directory: %s", tools_dir)

    # Iterate through all Python files in the tools directory
    loaded_count = 0
    failed_count = 0

    for _, module_name, _ in pkgutil.iter_modules([tools_dir]):
        if module_name.startswith("__"):
            logger.debug("Skipping module: %s", module_name)
            continue

        try:
            # Import the module
            logger.debug("Importing tool module: %s", module_name)
            module = importlib.import_module(
                f".tools.{module_name}", package="mcp_ollama_python"
            )

            # Check if module exports tool_definition
            if not hasattr(module, "tool_definition"):
                logger.warning(
                    "Module %s has no tool_definition, skipping", module_name
                )
                continue

            tool_def = getattr(module, "tool_definition")

            # Convert dict to ToolDefinition if needed
            if isinstance(tool_def, dict):
                try:
                    tool_def = ToolDefinition(**tool_def)
                    logger.debug("Converted dict to ToolDefinition for %s", module_name)
                except Exception as e:
                    logger.error(
                        "Failed to convert tool_definition to ToolDefinition in %s: %s",
                        module_name,
                        e,
                    )
                    failed_count += 1
                    continue

            if isinstance(tool_def, ToolDefinition):
                # Find the handler function (should end with _handler)
                handler = None
                for attr_name in dir(module):
                    if attr_name.endswith("_handler") and callable(
                        getattr(module, attr_name)
                    ):
                        handler = getattr(module, attr_name)
                        logger.debug("Found handler: %s in %s", attr_name, module_name)
                        break

                if handler:
                    registry.register(tool_def, handler)
                    loaded_count += 1
                    logger.info("Loaded tool: %s from %s", tool_def.name, module_name)
                else:
                    logger.warning(
                        "Tool %s in %s has no handler function",
                        tool_def.name,
                        module_name,
                    )
                    failed_count += 1
            else:
                logger.warning(
                    "tool_definition in %s is not a ToolDefinition instance",
                    module_name,
                )
                failed_count += 1

        except Exception as e:
            logger.error("Failed to load tool %s: %s", module_name, e, exc_info=True)
            failed_count += 1
            continue

    logger.info(
        "Tool discovery complete: %d loaded, %d failed", loaded_count, failed_count
    )
    return registry
