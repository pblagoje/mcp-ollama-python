# 🦙 Ollama MCP Server (Python)

**Supercharge your AI assistant with local LLM access**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Poetry](https://img.shields.io/badge/Poetry-1.0+-blue)](https://python-poetry.org)
[![MCP](https://img.shields.io/badge/MCP-1.0-green)](https://github.com/anthropics/model-context-protocol)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python [MCP](https://github.com/anthropics/model-context-protocol) server that exposes your local [Ollama](https://ollama.ai) models as tools for AI assistants like **Windsurf**, **VS Code**, **Claude Desktop**, and more.

📚 **[Full Documentation](https://pblagoje.github.io/mcp-ollama-python/)**

---

## What It Does

Connect your local LLMs to any MCP-compatible AI assistant. No cloud APIs needed.

| Tool | What it does |
|------|-------------|
| `ollama_chat` | Chat with any local model (multi-turn, tool-calling) |
| `ollama_generate` | Generate text completions |
| `ollama_embed` | Create vector embeddings |
| `ollama_list` | List installed models |
| `ollama_show` | Inspect model details |
| `ollama_pull` | Download new models |
| `ollama_delete` | Remove models |
| `ollama_ps` | List running models |

## Quick Start

**Prerequisites:** Python 3.10+, [Ollama](https://ollama.ai) running locally

```bash
pip install mcp-ollama-python
```

### Windsurf / VS Code

Add to your MCP config (`mcp_config.json`):

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

Restart your editor — done. Your AI assistant can now use local Ollama models.

### Try It

Type in your AI assistant's chat:

> **MCP Tool: ollama / ollama_chat** — Use model llama3.1 and explain quantum computing

## Key Features

- 🔧 **8 MCP tools** — Full Ollama SDK access
- 🔄 **Hot-swap architecture** — Drop a file in `tools/`, it's auto-discovered
- 🎯 **Type-safe** — Pydantic models throughout
- 🚀 **Lightweight** — Minimal dependencies, fast startup
- 🔌 **Universal** — Works with any MCP client

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](https://pblagoje.github.io/mcp-ollama-python/installation/) | Setup and prerequisites |
| [Available Tools](https://pblagoje.github.io/mcp-ollama-python/tools/) | All tools with examples |
| [Configuration](https://pblagoje.github.io/mcp-ollama-python/configuration/) | Environment variables, model config |
| [Windsurf Integration](https://pblagoje.github.io/mcp-ollama-python/windsurf/) | Complete Windsurf setup guide |
| [VS Code Integration](https://pblagoje.github.io/mcp-ollama-python/vscode/) | VS Code setup |
| [Architecture](https://pblagoje.github.io/mcp-ollama-python/architecture/) | How it works, adding tools |
| [Server Control](https://pblagoje.github.io/mcp-ollama-python/SERVER_CONTROL/) | Start/stop/manage the server |
| [Interactive Manager](https://pblagoje.github.io/mcp-ollama-python/mcp_interactive/) | Menu-driven management UI |
| [Development](https://pblagoje.github.io/mcp-ollama-python/development/) | Contributing, code quality |

## License

[MIT](LICENSE)

---

<div align="center">

Made with ❤️ using Python, Poetry, and Ollama

</div>
