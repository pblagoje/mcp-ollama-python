# Architecture

## Hot-Swap Autoloader

This server uses a **hot-swap autoloader** pattern for tool discovery:

```
src/mcp_ollama_python/
├── main.py              # Entry point
├── server.py            # MCP server creation
├── autoloader.py        # Dynamic tool discovery
├── ollama_client.py     # Ollama HTTP client
├── models.py            # Pydantic type definitions
├── response_formatter.py # Response formatting
└── tools/               # Tool implementations
    ├── chat.py          # Each exports tool_definition
    ├── generate.py
    ├── embed.py
    ├── list.py
    ├── show.py
    ├── pull.py
    ├── delete.py
    └── ps.py
```

**Key Benefits:**

- Add new tools by dropping files in `src/mcp_ollama_python/tools/`
- Zero server code changes required
- Each tool is independently testable

## Adding a New Tool

1. Create `src/mcp_ollama_python/tools/your_tool.py`:

```python
from typing import Dict, Any
from ..models import ToolDefinition, ResponseFormat
from ..ollama_client import OllamaClient
from ..response_formatter import format_response

async def your_tool_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Your tool implementation"""
    # Implementation here
    return format_response({"result": "success"}, format)

# Tool definition
tool_definition = ToolDefinition(
    name="ollama_your_tool",
    description="Your tool description",
    input_schema={
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        },
        "required": ["param"]
    },
)
```

2. Done! The autoloader discovers it automatically.

## Scripts Package

Management scripts live in `src/mcp_ollama_python/scripts/`:

```
src/mcp_ollama_python/scripts/
├── __init__.py          # Package marker
├── mcp_interactive.py   # Interactive menu manager
└── server_control.py    # CLI server control
```

These are exposed as Poetry entry points:

- `mcp-interactive` → `mcp_ollama_python.scripts.mcp_interactive:main`
- `mcp-server-control` → `mcp_ollama_python.scripts.server_control:main`
