"""
Ollama MCP Server - Main entry point
"""

import asyncio
import signal
import sys
from typing import Optional
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
    print(f"Error: mcp package import failed: {e}")
    print("Please install it with: pip install mcp")
    sys.exit(1)


# Global server instance for signal handling
_server_instance: Optional[Server] = None
_shutdown_event: Optional[asyncio.Event] = None


def safe_print(*args, **kwargs):
    """Safe print that handles closed stdout/stderr"""
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        # stdout/stderr is closed, ignore
        pass


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    safe_print(f"\nReceived signal {signum}, shutting down gracefully...")
    if _shutdown_event:
        _shutdown_event.set()


async def main():
    """Main function to start the MCP server"""
    global _server_instance, _shutdown_event
    
    # Create shutdown event
    _shutdown_event = asyncio.Event()
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize Ollama client
    ollama_client = OllamaClient()

    # Initialize our MCP server
    server = OllamaMCPServer(ollama_client)

    # Create MCP server instance
    mcp_server = Server("ollama-mcp")
    _server_instance = mcp_server
    
    safe_print("Starting Ollama MCP Server...")
    safe_print("Press Ctrl+C to stop the server")

    @mcp_server.list_tools()
    async def handle_list_tools() -> list[MCPTool]:
        """Handle list_tools request"""
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
        return tools

    @mcp_server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> list[TextContent]:
        """Handle call_tool request"""
        result = await server.handle_call_tool(name, arguments)

        content = []
        for item in result["content"]:
            if item["type"] == "text":
                content.append(TextContent(type="text", text=item["text"]))

        return content

    @mcp_server.list_resources()
    async def handle_list_resources() -> list[Resource]:
        """Handle list_resources request"""
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
        return resources

    @mcp_server.read_resource()
    async def handle_read_resource(uri: str) -> str:
        """Handle read_resource request"""
        result = await server.handle_read_resource(uri)
        if result.get("contents"):
            return result["contents"][0].get("text", "")
        return ""

    @mcp_server.list_prompts()
    async def handle_list_prompts() -> list[Prompt]:
        """Handle list_prompts request"""
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
        return prompts

    @mcp_server.get_prompt()
    async def handle_get_prompt(name: str, arguments: Optional[dict] = None) -> dict:
        """Handle get_prompt request"""
        result = await server.handle_get_prompt(name, arguments)
        return result

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
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
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
        safe_print("\nServer interrupted by user")
    except Exception as e:
        safe_print(f"Server error: {e}")
        raise
    finally:
        # Cleanup
        await ollama_client.client.aclose()
        safe_print("Cleanup completed.")


def run():
    """Entry point for the mcp-ollama-python command"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        safe_print("\nShutdown complete.")
        sys.exit(0)
    except Exception as e:
        safe_print(f"Fatal error: {e}")
        sys.exit(1)


def stop():
    """Stop the running server (for programmatic control)"""
    if _shutdown_event:
        _shutdown_event.set()
        safe_print("Stop signal sent to server")
    else:
        safe_print("No server instance running")


if __name__ == "__main__":
    run()
