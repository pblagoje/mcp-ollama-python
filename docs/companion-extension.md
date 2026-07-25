# Companion VS Code Extension

This MCP server (`mcp-ollama-python`) is the **backend**. For day-to-day use in Visual Studio Code, install the companion extension:

| | |
|---|---|
| **Repository** | [github.com/pblagoje/mcp-ollama-extension](https://github.com/pblagoje/mcp-ollama-extension) |
| **Documentation** | [pblagoje.github.io/mcp-ollama-extension](https://pblagoje.github.io/mcp-ollama-extension/) |
| **Marketplace** | [MCP Ollama Manager](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension) (`internetics.mcp-ollama-extension`) |

## What the extension adds

- Start / stop / restart the MCP server from the Command Palette or status bar
- Ollama models tree in the Explorer sidebar
- Pull / delete models, chat, generate, embeddings, explain code, write docstring
- Server and extension log viewers
- Settings for Ollama host, Python path, and log levels

## What you still need

1. `pip install mcp-ollama-python` (this package)
2. [Ollama](https://ollama.ai/) running
3. The extension installed in VS Code / compatible editors that support VS Code extensions

The extension does **not** replace this package — it launches and talks to it over MCP stdio.

## Without the extension

You can still use this server with any MCP client by adding it to MCP config. See [Installation](installation.md) and [VS Code Integration](vscode.md).

## Issue tracker

- Extension UI / VS Code commands → [mcp-ollama-extension issues](https://github.com/pblagoje/mcp-ollama-extension/issues)
- MCP tools / Python server → [mcp-ollama-python issues](https://github.com/pblagoje/mcp-ollama-python/issues)
