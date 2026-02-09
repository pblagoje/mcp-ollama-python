# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server endpoint |
| `OLLAMA_API_KEY` | — | API key for Ollama Cloud (when implemented) |

### Custom Ollama Host

```bash
export OLLAMA_HOST="http://localhost:11434"
py -m poetry run mcp-ollama-python
```

### Ollama Cloud Configuration (Planned)

```bash
export OLLAMA_HOST="https://ollama.com"
export OLLAMA_API_KEY="your-ollama-cloud-api-key"
py -m poetry run mcp-ollama-python
```

## MCP Model Configuration

The server exposes local Ollama models through MCP. Configure available models in `mcp.json`:

**`mcp-ollama-python/mcp.json`**
```json
{
  "capabilities": {
    "models": [
      {
        "name": "gpt-oss",
        "provider": "ollama",
        "description": "Local Ollama GPT-OSS model served through MCP",
        "maxTokens": 4096
      }
    ]
  }
}
```

**Model Configuration Options:**

- `name` — Model identifier used by MCP clients
- `provider` — Always `"ollama"` for this server
- `description` — Human-readable model description
- `maxTokens` — Maximum context window size

### Multiple Models

You can expose multiple Ollama models through MCP:

```json
{
  "capabilities": {
    "models": [
      {
        "name": "gpt-oss",
        "provider": "ollama",
        "description": "Local Ollama GPT-OSS model",
        "maxTokens": 4096
      },
      {
        "name": "llama3.2",
        "provider": "ollama",
        "description": "Llama 3.2 model for general tasks",
        "maxTokens": 8192
      },
      {
        "name": "codellama",
        "provider": "ollama",
        "description": "Code Llama for programming tasks",
        "maxTokens": 16384
      }
    ]
  }
}
```
