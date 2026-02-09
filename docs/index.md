# Ollama MCP Server (Python)

**Supercharge your AI assistant with local LLM access**

A Python implementation of the [Model Context Protocol](https://github.com/anthropics/model-context-protocol) (MCP) server that exposes [Ollama](https://ollama.ai) SDK functionality as MCP tools, enabling seamless integration between your local LLM models and MCP-compatible applications like Windsurf and VS Code.

This is a Python port of the [TypeScript ollama-mcp](https://github.com/rawveg/ollama-mcp) project.

---

## Features

- :cloud: **Ollama Cloud Support** — Full integration with Ollama's cloud platform
- :wrench: **8 Comprehensive Tools** — Full access to Ollama's SDK functionality
- :arrows_counterclockwise: **Hot-Swap Architecture** — Automatic tool discovery with zero-config
- :dart: **Type-Safe** — Built with Pydantic models and type hints
- :rocket: **Minimal Dependencies** — Lightweight and fast
- :electric_plug: **Drop-in Integration** — Works with Windsurf, VS Code, and other MCP clients
- :globe_with_meridians: **Web Search & Fetch** — Real-time web search and content extraction via Ollama Cloud (planned)
- :twisted_rightwards_arrows: **Hybrid Mode** — Use local and cloud models seamlessly in one server

## Why Python?

This Python implementation provides the same functionality as the TypeScript version but with:

- **Python Native** — No Node.js dependencies required
- **Poetry Package Management** — Modern Python dependency management
- **Async/Await** — Native Python async support
- **Pydantic Models** — Robust data validation and type safety
- **Poetry Scripts** — Easy installation and execution

## Quick Example

Type in your MCP-compatible chat window:

- **MCP Tool: ollama / ollama_chat** — Use model llava and tell me a bed time story
- **MCP Tool: ollama / ollama_chat** — Use model gpt-oss and tell me a bed time story

## Next Steps

- [Installation Guide](installation.md) — Get up and running in minutes
- [Available Tools](tools.md) — See all 8 MCP tools
- [Windsurf Integration](windsurf.md) — Set up with Windsurf IDE
- [VS Code Integration](vscode.md) — Set up with VS Code
