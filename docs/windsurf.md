# Windsurf Integration

Windsurf is an AI-powered code editor that supports MCP servers. This guide provides complete setup instructions for integrating the Ollama MCP server with Windsurf.

## Step 1: Configure MCP Server

Add the Ollama MCP server to your Windsurf MCP configuration:

**`%USERPROFILE%\.codeium\windsurf\mcp_config.json`** (Windows)
**`~/.codeium/windsurf/mcp_config.json`** (macOS/Linux)

```json
{
  "mcpServers": {
    "ollama": {
      "command": "py",
      "args": ["-m", "mcp_ollama_python"],
      "disabled": false,
      "env": {}
    },
    "git": {
      "command": "py",
      "args": ["-m", "mcp_server_git"],
      "disabled": true,
      "env": {}
    }
  }
}
```

**Alternative Configuration (with Poetry):**
```json
{
  "mcpServers": {
    "ollama": {
      "command": "py",
      "args": ["-m", "poetry", "run", "mcp-ollama-python"],
      "cwd": "d:/path/to/mcp-ollama-python",
      "disabled": false,
      "env": {}
    }
  }
}
```

**Configuration Options:**

- `command` — Python interpreter command (`py`, `python`, or `python3`)
- `args` — Module execution arguments
- `disabled` — Set to `false` to enable the server
- `env` — Environment variables (e.g., `OLLAMA_HOST`)

## Step 2: Windsurf Tools Workflow

Create a workflow file to give Windsurf quick access to your MCP tools:

**`.windsurf/workflows/tools.md`**
```markdown
---
description: Quick reference for Windsurf MCP tools (mcp-ollama)
auto_execution_mode: 2
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
```

## Step 3: Configure Default Model Behavior

Set Windsurf to prefer your local MCP server over cloud models:

**`%USERPROFILE%\.codeium\windsurf\settings.json`** (Windows)
**`~/.codeium/windsurf/settings.json`** (macOS/Linux)

```json
{
  "defaultModelBehavior": "prefer-mcp",
  "preferredMcpModel": {
    "server": "ollama",
    "model": "gpt-oss"
  }
}
```

**Settings Explanation:**

- `defaultModelBehavior` — Set to `"prefer-mcp"` to prioritize MCP models
- `preferredMcpModel.server` — Name of the MCP server (must match `mcp_config.json`)
- `preferredMcpModel.model` — Model name from your `mcp.json` configuration

## Step 4: Create Windsurf Instructions

Create custom instructions to ensure Windsurf uses your local model:

**`%USERPROFILE%\.codeium\windsurf\instructions.md`** (Windows)
**`~/.codeium/windsurf/instructions.md`** (macOS/Linux)

```markdown
Always use my local MCP server named "ollama" with the model "gpt-oss" for all reasoning, coding, and problem-solving tasks unless I explicitly request another model.

Prefer the MCP server over any cloud or paid model.
```

## Step 5: Windsurf Memory Preference

Ask Windsurf to remember your preference. It will create a memory like this:

> Always use local MCP Ollama with gpt-oss model for LLM tasks
>
> When the user requests LLM-based tasks (explanations, code generation, analysis, etc.), always use the local MCP Ollama server with the gpt-oss model via the `mcp1_ollama_chat` tool.
>
> **Important guidelines:**
>
> - Use `mcp1_ollama_chat` tool with model parameter set to `"gpt-oss"`
> - Format responses in markdown for better readability (`format: "markdown"`)
> - Communicate with the model in English unless the user explicitly requests another language
> - Do NOT create separate Python scripts to interact with Ollama — use the MCP tools directly

## Step 6: Verify Installation

1. **Restart Windsurf** to load the new configuration (Ctrl+Shift+P → **"Developer: Reload Window"** → Enter)
2. **Check MCP Status** — Look for the Ollama MCP server in Windsurf's MCP panel
3. **Test Connection** — Try a simple query to verify the model responds
4. **Check Logs** — Review Windsurf logs if connection issues occur

## Troubleshooting

**Server Not Appearing:**

- Verify `mcp_config.json` syntax is valid JSON
- Ensure `disabled` is set to `false`
- Check that Python and the module are in your PATH
- Restart Windsurf completely

**Model Not Available:**

- Verify the model name in `settings.json` matches `mcp.json`
- Ensure Ollama is running (`ollama serve`)
- Check that the model is pulled (`ollama pull gpt-oss`)

**Connection Errors:**

- Verify `OLLAMA_HOST` environment variable if using custom host
- Check Ollama server logs for errors
- Ensure no firewall blocking localhost connections
