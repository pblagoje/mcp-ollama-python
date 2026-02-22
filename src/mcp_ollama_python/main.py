"""
Ollama MCP Server - Main entry point
"""

import asyncio
import logging
import signal
import sys
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Use absolute imports so PyInstaller/standalone execution works even when __package__ is not set
try:
    from mcp_ollama_python.server import OllamaMCPServer
    from mcp_ollama_python.ollama_client import OllamaClient
except ImportError:
    from .server import OllamaMCPServer
    from .ollama_client import OllamaClient

try:
    from mcp.server import Server
    from mcp.types import (
        TextContent,
        Tool as MCPTool,
        Resource,
        Prompt,
    )
    from mcp.server.stdio import stdio_server
except ImportError as e:
    logger.error("MCP package import failed: %s", e)
    print(f"Error: mcp package import failed: {e}")
    print("Please install it with: pip install mcp")
    sys.exit(1)


# Global server instance for signal handling
_server_instance: Optional[Server] = None
_shutdown_event: Optional[asyncio.Event] = None


def safe_print(*args, **kwargs) -> None:
    """
    Safe print that handles closed stdout/stderr.

    Args:
        *args: Arguments to print
        **kwargs: Keyword arguments for print function
    """
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        # stdout/stderr is closed, ignore
        pass


def signal_handler(signum: int, frame) -> None:
    """
    Handle shutdown signals gracefully.

    Args:
        signum: Signal number received
        frame: Current stack frame
    """
    # Only perform signal-safe operations - set the shutdown event
    if _shutdown_event:
        _shutdown_event.set()


async def main() -> None:
    """
    Main function to start the MCP server.

    Initializes the Ollama client, MCP server, and handles graceful shutdown.
    Registers handlers for tools, resources, and prompts.
    """
    global _server_instance, _shutdown_event

    logger.info("Initializing Ollama MCP Server")

    # Create shutdown event
    _shutdown_event = asyncio.Event()

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Ollama client
    try:
        ollama_client = OllamaClient()
        logger.info("Ollama client initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize Ollama client: %s", e)
        raise

    # Initialize our MCP server
    server = OllamaMCPServer(ollama_client)

    # Create MCP server instance
    mcp_server = Server("ollama-mcp")
    _server_instance = mcp_server

    safe_print("Starting Ollama MCP Server...")
    safe_print("Press Ctrl+C to stop the server")

    @mcp_server.list_tools()
    async def handle_list_tools() -> list[MCPTool]:
        """
        Handle list_tools request.

        Returns:
            List of available MCP tools
        """
        try:
            result = await server.handle_list_tools()
            tools = []
            for tool_data in result["tools"]:
                tools.append(
                    MCPTool(
                        name=tool_data["name"],
                        description=tool_data["description"],
                        inputSchema=tool_data["inputSchema"],
                    )
                )
            logger.debug("Listed %d tools", len(tools))
            return tools
        except Exception as e:
            logger.error("Error listing tools: %s", e)
            raise

    @mcp_server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """
        Handle call_tool request.

        Args:
            name: Name of the tool to call
            arguments: Arguments for the tool

        Returns:
            List of text content responses
        """
        try:
            logger.debug("Calling tool: %s", name)
            result = await server.handle_call_tool(name, arguments)

            content = []
            for item in result["content"]:
                if item["type"] == "text":
                    content.append(TextContent(type="text", text=item["text"]))

            return content
        except Exception as e:
            logger.error("Error calling tool %s: %s", name, e)
            raise

    @mcp_server.list_resources()
    async def handle_list_resources() -> list[Resource]:
        """
        Handle list_resources request.

        Returns:
            List of available resources
        """
        try:
            result = await server.handle_list_resources()
            resources = []
            for resource_data in result["resources"]:
                resources.append(
                    Resource(
                        uri=resource_data["uri"],
                        name=resource_data["name"],
                        description=resource_data.get("description"),
                        mimeType=resource_data.get("mimeType", "text/plain"),
                    )
                )
            logger.debug("Listed %d resources", len(resources))
            return resources
        except Exception as e:
            logger.error("Error listing resources: %s", e)
            raise

    @mcp_server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """
        Handle read_resource request.

        Args:
            uri: URI of the resource to read

        Returns:
            Resource content as string
        """
        try:
            logger.debug("Reading resource: %s", uri)
            result = await server.handle_read_resource(uri)
            if result.get("contents"):
                return result["contents"][0].get("text", "")
            return ""
        except Exception as e:
            logger.error("Error reading resource %s: %s", uri, e)
            raise

    @mcp_server.list_prompts()
    async def handle_list_prompts() -> list[Prompt]:
        """
        Handle list_prompts request.

        Returns:
            List of available prompts
        """
        try:
            result = await server.handle_list_prompts()
            prompts = []
            for prompt_data in result["prompts"]:
                prompts.append(
                    Prompt(
                        name=prompt_data["name"],
                        description=prompt_data.get("description"),
                        arguments=prompt_data.get("arguments", []),
                    )
                )
            logger.debug("Listed %d prompts", len(prompts))
            return prompts
        except Exception as e:
            logger.error("Error listing prompts: %s", e)
            raise

    @mcp_server.get_prompt()
    async def handle_get_prompt(name: str, arguments: Optional[dict] = None) -> dict:
        """
        Handle get_prompt request.

        Args:
            name: Name of the prompt to get
            arguments: Optional arguments for the prompt

        Returns:
            Prompt data dictionary
        """
        try:
            logger.debug("Getting prompt: %s", name)
            result = await server.handle_get_prompt(name, arguments)
            return result
        except Exception as e:
            logger.error("Error getting prompt %s: %s", name, e)
            raise

    # Run the server with graceful shutdown support
    try:
        async with stdio_server() as (read_stream, write_stream):
            safe_print("Server started successfully!")
            safe_print("Waiting for MCP client connections...")

            # Create server task
            server_task = asyncio.create_task(
                mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
            )

            # Wait for either server completion or shutdown signal
            shutdown_task = asyncio.create_task(_shutdown_event.wait())
            done, pending = await asyncio.wait(
                [server_task, shutdown_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            safe_print("Server stopped.")

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
        safe_print("\nServer interrupted by user")
    except Exception as e:
        logger.error("Server error: %s", e, exc_info=True)
        safe_print(f"Server error: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Cleaning up resources")
        await ollama_client.client.aclose()
        safe_print("Cleanup completed.")


def run() -> None:
    """
    Entry point for the mcp-ollama-python command.

    Runs the async main function and handles shutdown gracefully.
    """
    try:
        logger.info("Starting mcp-ollama-python")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown complete")
        safe_print("\nShutdown complete.")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        safe_print(f"Fatal error: {e}")
        sys.exit(1)


def stop() -> None:
    """
    Stop the running server (for programmatic control).

    Sets the shutdown event to trigger graceful server shutdown.
    """
    if _shutdown_event:
        logger.info("Stop signal sent to server")
        _shutdown_event.set()
        safe_print("Stop signal sent to server")
    else:
        logger.warning("No server instance running")
        safe_print("No server instance running")


if __name__ == "__main__":
    run()
