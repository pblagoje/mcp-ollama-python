---
description: Quick reference for Windsurf MCP tools (mcp-ollama)
---

# MCP Tools (mcp-ollama)

Available tools exposed by the local `mcp-ollama-python` server:

- **ollama_chat** – Interactive chat with models (multi-turn, tool-calling, structured outputs)
- **ollama_list** – List installed models
- **ollama_show** – Show details for a specific model
- **ollama_generate** – Single-prompt text generation
- **ollama_pull** – Pull a model from a registry
- **ollama_delete** – Delete a local model
- **ollama_ps** – List running models
- **ollama_embed** – Create embeddings for input text
- **ollama_execute** – Execute a system command via the server (utility/test)

## How to list tools in Windsurf
1) Open the command palette and run: `MCP: List Tools`
2) Or run the MCP tool via the chat with: `/tools`

## Notes
- Server: local Ollama via `mcp-ollama-python`
- Formats: most tools accept `format` = `json` (default) or `markdown`
