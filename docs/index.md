# Ollama MCP Server (Python)

**Supercharge your AI assistant with local LLM access**

A Python implementation of the [Model Context Protocol](https://github.com/anthropics/model-context-protocol) (MCP) server that exposes [Ollama](https://ollama.ai) functionality as MCP tools for Windsurf, VS Code, Cursor, Claude Desktop, and other MCP clients.

| Resource | Link |
|----------|------|
| GitHub | [pblagoje/mcp-ollama-python](https://github.com/pblagoje/mcp-ollama-python) |
| PyPI | [mcp-ollama-python](https://pypi.org/project/mcp-ollama-python/) |
| Companion VS Code extension | [mcp-ollama-extension](https://github.com/pblagoje/mcp-ollama-extension) · [extension docs](https://pblagoje.github.io/mcp-ollama-extension/) · [Marketplace](https://marketplace.visualstudio.com/items?itemName=internetics.mcp-ollama-extension) |

---

## Ecosystem

```
VS Code extension (optional UI)
  mcp-ollama-extension
        │  stdio / MCP
        ▼
MCP server (this project)
  mcp-ollama-python
        │  HTTP :11434
        ▼
Ollama
```

- **This project** — the MCP server. Required for all clients.
- **[MCP Ollama Manager](https://github.com/pblagoje/mcp-ollama-extension)** — optional VS Code extension to start/stop the server, browse models, and view logs. See [VS Code Integration](vscode.md).

---

## Features

- **8 MCP tools** — chat, generate, embed, list, show, pull, delete, ps
- **Hot-swap architecture** — automatic tool discovery
- **Type-safe** — Pydantic models and type hints
- **Minimal dependencies** — lightweight and fast
- **Drop-in integration** — Windsurf, VS Code, and other MCP clients

## Quick Example

In an MCP-compatible chat:

- **MCP Tool: ollama / ollama_chat** — Use model llava and tell me a bed time story
- **MCP Tool: ollama / ollama_chat** — Use model gpt-oss and tell me a bed time story

## Next Steps

- [Installation Guide](installation.md) — Get up and running in minutes
- [Available Tools](tools.md) — See all MCP tools
- [Security](SECURITY.md) — Threat model and opt-in code execution
- [Windsurf Integration](windsurf.md) — Set up with Windsurf IDE
- [VS Code Integration](vscode.md) — MCP JSON config **or** the companion extension
- [Companion Extension](companion-extension.md) — How this server relates to the VS Code UI

## Related

- [mcp-ollama-extension](https://github.com/pblagoje/mcp-ollama-extension) — VS Code manager for this server
- [Ollama](https://ollama.ai/) — Run large language models locally
