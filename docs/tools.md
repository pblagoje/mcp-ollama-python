# Available Tools

The Ollama MCP server exposes 8 comprehensive tools for interacting with your local Ollama models.

## Model Management

| Tool | Description |
|------|-------------|
| `ollama_list` | List all available local models |
| `ollama_show` | Get detailed information about a specific model |
| `ollama_pull` | Download models from Ollama library |
| `ollama_delete` | Remove models from local storage |

## Model Operations

| Tool | Description |
|------|-------------|
| `ollama_ps` | List currently running models |
| `ollama_generate` | Generate text completions |
| `ollama_chat` | Interactive chat with models (supports tools/functions) |
| `ollama_embed` | Generate embeddings for text |

## Web Tools (Ollama Cloud — Planned)

| Tool | Description |
|------|-------------|
| `ollama_web_search` | Search the web with customizable result limits |
| `ollama_web_fetch` | Fetch and parse web page content |

## Output Formats

Most tools accept a `format` parameter:

- `json` (default) — Structured JSON output
- `markdown` — Human-readable Markdown output

## Quick Reference

**List models:**
```json
{ "tool": "ollama_list", "arguments": { "format": "markdown" } }
```

**Chat with a model:**
```json
{
  "tool": "ollama_chat",
  "arguments": {
    "model": "llama3.2:latest",
    "messages": [{ "role": "user", "content": "Hello!" }]
  }
}
```

**Generate text:**
```json
{
  "tool": "ollama_generate",
  "arguments": {
    "model": "llama3.1",
    "prompt": "Explain quantum computing in simple terms"
  }
}
```

**Generate embeddings:**
```json
{
  "tool": "ollama_embed",
  "arguments": {
    "model": "nomic-embed-text",
    "input": ["Hello world", "Embeddings are great"]
  }
}
```
