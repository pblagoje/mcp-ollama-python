# Installation

## Prerequisites

- **Python 3.10+**
- **Ollama** running locally — [Download Ollama](https://ollama.ai)

## Install from PyPI

```bash
pip install mcp-ollama-python
```

That's it. Your MCP client (Windsurf, VS Code, etc.) will start the server automatically — you don't need to run it manually.

## Configure Your IDE

### VS Code — companion extension (recommended)

Install [MCP Ollama Manager](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension), then start the server from the Command Palette.  
See [Companion VS Code Extension](companion-extension.md) and [VS Code Integration](vscode.md).

### Windsurf

Add to **`%USERPROFILE%\.codeium\windsurf\mcp_config.json`** (Windows) or **`~/.codeium\windsurf\mcp_config.json`** (macOS/Linux):

```json
{
  "mcpServers": {
    "ollama": {
      "command": "py",
      "args": ["-m", "mcp_ollama_python"],
      "disabled": false
    }
  }
}
```

Restart Windsurf — the Ollama MCP server will appear in the MCP panel.

See the full [Windsurf Integration](windsurf.md) guide for advanced setup.

### VS Code / Cursor — MCP JSON only

Add to your MCP settings:

```json
{
  "mcpServers": {
    "ollama": {
      "command": "py",
      "args": ["-m", "mcp_ollama_python"],
      "disabled": false
    }
  }
}
```

See the full [VS Code Integration](vscode.md) guide for details.

## Windows Executable

If you prefer a standalone `.exe` (no Python required), download it from the [Releases](https://github.com/pblagoje/mcp-ollama-python/releases) page.

## Verify Installation

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Verify the module is installed
py -m mcp_ollama_python --help
```

## Next Steps

- [Configuration](configuration.md) — Environment variables, custom hosts, model config
- [Available Tools](tools.md) — All 8 MCP tools with examples
