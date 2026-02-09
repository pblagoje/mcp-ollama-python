# VS Code Integration

## MCP Configuration

Add the Ollama MCP server to your VS Code MCP settings:

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

- [Available Tools](tools.md) — Full list of MCP tools and their arguments
- [Configuration](configuration.md) — Environment variables and model configuration
