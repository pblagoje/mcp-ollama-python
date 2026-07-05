# Security

This document describes the threat model and security controls for **mcp-ollama-python**.

## Trust model

The MCP server runs as a **local subprocess** of your editor (Cursor, Windsurf, VS Code, etc.). Any MCP client connected to it can invoke all exposed tools. Treat the MCP client and anyone who can edit its configuration as **trusted**.

The server talks to **Ollama** over HTTP. By default it only connects to loopback hosts (`127.0.0.1`, `localhost`, `host.docker.internal`).

## Controls (v1.0.8+)

| Area | Control |
|------|---------|
| `OLLAMA_HOST` | Validated URL; no embedded credentials; no path/query; loopback-only unless `OLLAMA_ALLOW_REMOTE_HOST=1`; blocks link-local/metadata IPs when remote is allowed |
| HTTP client | Redirects disabled (`follow_redirects=False`) to reduce SSRF via redirect chains |
| Model names | Restricted to safe character set before API calls |
| `ollama_execute` | **Disabled by default**; set `OLLAMA_EXECUTE_ENABLED=1` to register the tool; shell/bash removed; 64 KiB code limit; 30s timeout; minimal subprocess environment; runs in a temp directory |
| Chat/embed input | Message count, content length, and embed batch sizes capped |
| Interactive manager | Environment variable keys allowlisted; `OLLAMA_HOST` re-validated on save/load |
| Data directory | `~/.mcp-ollama-python/` created with restrictive permissions for PID/logs/config files |

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API base URL |
| `OLLAMA_ALLOW_REMOTE_HOST` | unset | Set to `1` to allow LAN/remote Ollama hosts |
| `OLLAMA_EXECUTE_ENABLED` | unset | Set to `1` to expose `ollama_execute` |
| `OLLAMA_API_KEY` | unset | Bearer token for authenticated Ollama endpoints |
| `OLLAMA_MODELS` | unset | Custom models directory (passed through to Ollama) |

Only the variables above may be stored via **mcp-interactive** (`~/.mcp-ollama-python/tmp/.mcp_env_vars.json`).

## Risky operations

These tools can affect your machine or network when invoked by an MCP client:

- **`ollama_pull`** — downloads large model files
- **`ollama_delete`** — removes local models
- **`ollama_execute`** — runs arbitrary code (opt-in only)

Use MCP only with clients and workflows you trust. Do not enable `OLLAMA_EXECUTE_ENABLED` on shared or production systems.

## Reporting issues

Please report security issues via [GitHub Security Advisories](https://github.com/pblagoje/mcp-ollama-python/security/advisories) for the repository.
