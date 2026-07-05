# Configuration

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server endpoint (loopback only unless remote is allowed) |
| `OLLAMA_ALLOW_REMOTE_HOST` | — | Set to `1` to allow non-local `OLLAMA_HOST` values (LAN/remote Ollama) |
| `OLLAMA_EXECUTE_ENABLED` | — | Set to `1` to expose the `ollama_execute` tool (disabled by default) |
| `OLLAMA_API_KEY` | — | API key for authenticated Ollama endpoints |
| `OLLAMA_MODELS` | — | Custom models directory |

See [Security](SECURITY.md) for the full threat model and allowlists.

### Custom Ollama Host (local)

```bash
export OLLAMA_HOST="http://localhost:11434"
py -m poetry run mcp-ollama-python
```

### Remote or LAN Ollama

```bash
export OLLAMA_ALLOW_REMOTE_HOST=1
export OLLAMA_HOST="http://192.168.1.50:11434"
py -m poetry run mcp-ollama-python
```

### Enable code execution (opt-in)

`ollama_execute` is **not registered** unless you explicitly enable it:

```bash
export OLLAMA_EXECUTE_ENABLED=1
py -m poetry run mcp-ollama-python
```

Shell/bash execution is not supported. Use only on trusted machines.

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
