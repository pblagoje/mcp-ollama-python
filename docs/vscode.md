# VS Code Integration

You can use **mcp-ollama-python** in VS Code in two ways:

1. **Companion extension (recommended)** — UI for start/stop, models, and logs  
2. **MCP config only** — wire the server into the editor’s MCP settings JSON

## Companion extension (recommended)

Install **MCP Ollama Manager**:

- [Marketplace](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension)
- [GitHub](https://github.com/pblagoje/mcp-ollama-extension)
- [Extension docs](https://pblagoje.github.io/mcp-ollama-extension/)

Then:

1. `pip install mcp-ollama-python` (or use the extension’s **Install Now** prompt)
2. Command Palette → **MCP Ollama: Configure Server**
3. **MCP Ollama: Start Server**

More detail: [Companion VS Code Extension](companion-extension.md).

## MCP Configuration (without the extension)

Add the Ollama MCP server to your VS Code / Cursor MCP settings:

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

On Linux/macOS you may prefer `"command": "python3"` instead of `"py"`.

## Usage Examples

### Chat with a Model

```json
{
  "tool": "ollama_chat",
  "arguments": {
    "model": "llama3.2:latest",
    "messages": [
      { "role": "user", "content": "Explain quantum computing" }
    ]
  }
}
```

### Generate Embeddings

```json
{
  "tool": "ollama_embed",
  "arguments": {
    "model": "nomic-embed-text",
    "input": ["Hello world", "Embeddings are great"]
  }
}
```

### List Available Models

```json
{
  "tool": "ollama_list",
  "arguments": {
    "format": "markdown"
  }
}
```

## Related

- [Companion VS Code Extension](companion-extension.md)
- [Available Tools](tools.md) — Full list of MCP tools and their arguments
- [Configuration](configuration.md) — Environment variables and model configuration
- [Extension documentation](https://pblagoje.github.io/mcp-ollama-extension/)
