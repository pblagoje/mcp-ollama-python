# 🦙 Ollama MCP Server (Python)

**Supercharge your AI assistant with local LLM access**

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![Poetry](https://img.shields.io/badge/Poetry-1.0+-blue)](https://python-poetry.org)
[![MCP](https://img.shields.io/badge/MCP-1.0-green)](https://github.com/anthropics/model-context-protocol)

A Python implementation of the MCP (Model Context Protocol) server that exposes Ollama SDK functionality as MCP tools, enabling seamless integration between your local LLM models and MCP-compatible applications like Windsurf and VS Code.

This is a Python port of the [TypeScript ollama-mcp](https://github.com/rawveg/ollama-mcp) project.

[Features](#-features) • [Installation](#-installation) • [Available Tools](#-available-tools) • [Configuration](#-configuration) • [Windsurf Integration](#-windsurf-integration) • [Usage](#-usage) • [Development](#-development)

---

## Example of usage

Type in the chat window:

- **MCP Tool: ollama / ollama_chat**. Use model llava and tell me a bed time story

- **MCP Tool: ollama / ollama_chat**. Use model gpt-oss and tell me a bed time story

---

## ✨ Features

- ☁️ **Ollama Cloud Support** - Full integration with Ollama's cloud platform
- 🔧 **8 Comprehensive Tools** - Full access to Ollama's SDK functionality
- 🔄 **Hot-Swap Architecture** - Automatic tool discovery with zero-config
- 🎯 **Type-Safe** - Built with Pydantic models and type hints
- 📊 **High Test Coverage** - Comprehensive test suite (planned)
- 🚀 **Minimal Dependencies** - Lightweight and fast
- 🔌 **Drop-in Integration** - Works with Windsurf, VS Code, and other MCP clients
- 🌐 **Web Search & Fetch** - Real-time web search and content extraction via Ollama Cloud (planned)
- 🔀 **Hybrid Mode** - Use local and cloud models seamlessly in one server

## 💡 Why Python?

This Python implementation provides the same functionality as the TypeScript version but with:

- **Python Native**: No Node.js dependencies required
- **Poetry Package Management**: Modern Python dependency management
- **Async/Await**: Native Python async support
- **Pydantic Models**: Robust data validation and type safety
- **Poetry Scripts**: Easy installation and execution

## 📦 Installation

### Prerequisites

- Python 3.10+
- Poetry (for development)
- Ollama running locally

### Quick Install with Poetry

```bash
# Clone the repository
git clone <repository-url>
cd mcp-ollama-python

# Install dependencies
py -m poetry install

# Run the server, run only if you wish to test using scripts, otherwise integration with Windsurf or VS Code will take care of it.
py -m poetry run mcp-ollama-python
```

### Manual Installation

```bash
# Install Poetry if you don't have it
curl -sSL https://install.python-poetry.org | python3 -

# Clone and install
git clone <repository-url>
cd mcp-ollama-python
poetry install

# Run the server, run only if you wish to test using scripts, otherwise integration with Windsurf or VS Code will take care of it.
poetry run mcp-ollama-python
```

## 🛠️ Generate a Windows executable if you specifically need it; otherwise, this step can be skipped.
cd ...mcp-ollama-python

poetry run pyinstaller mcp-ollama-python.spec --clean --distpath bin

## 🛠️ Available Tools

### Model Management
| Tool | Description |
|------|-------------|
| `ollama_list` | List all available local models |
| `ollama_show` | Get detailed information about a specific model |
| `ollama_pull` | Download models from Ollama library |
| `ollama_delete` | Remove models from local storage |

### Model Operations
| Tool | Description |
|------|-------------|
| `ollama_ps` | List currently running models |
| `ollama_generate` | Generate text completions |
| `ollama_chat` | Interactive chat with models (supports tools/functions) |
| `ollama_embed` | Generate embeddings for text |

### Web Tools (Ollama Cloud - Planned)
| Tool | Description |
|------|-------------|
| `ollama_web_search` | Search the web with customizable result limits |
| `ollama_web_fetch` | Fetch and parse web page content |

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server endpoint |
| `OLLAMA_API_KEY` | - | API key for Ollama Cloud (when implemented) |

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

### MCP Model Configuration

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
- `name`: Model identifier used by MCP clients
- `provider`: Always "ollama" for this server
- `description`: Human-readable model description
- `maxTokens`: Maximum context window size

You can add multiple models to expose different Ollama models through MCP:

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

## 🌊 Windsurf Integration

Windsurf is an AI-powered code editor that supports MCP servers. This section provides complete setup instructions for integrating the Ollama MCP server with Windsurf.

### Step 1: Configure MCP Server

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

Windsurf Tools setup file:
** .windsurf\workflows\tools.md
```
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

**Configuration Options:**
- `command`: Python interpreter command (`py`, `python`, or `python3`)
- `args`: Module execution arguments
- `disabled`: Set to `false` to enable the server
- `env`: Environment variables (e.g., `OLLAMA_HOST`)

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

### Step 2: Configure Default Model Behavior

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
- `defaultModelBehavior`: Set to `"prefer-mcp"` to prioritize MCP models
- `preferredMcpModel.server`: Name of the MCP server (must match `mcp_config.json`)
- `preferredMcpModel.model`: Model name from your `mcp.json` configuration

### Step 3: Create Windsurf Instructions

Create custom instructions to ensure Windsurf uses your local model:

**`%USERPROFILE%\.codeium\windsurf\instructions.md`** (Windows)
**`~/.codeium/windsurf/instructions.md`** (macOS/Linux)

```markdown
Always use my local MCP server named "ollama" with the model "gpt-oss" for all reasoning, coding, and problem-solving tasks unless I explicitly request another model.

Prefer the MCP server over any cloud or paid model.
```

### Step 4: Verify Installation

1. **Restart Windsurf** to load the new configuration (Ctrl-Shift; Search for **"Developer: Reload Window"**; Then hit Enter)
2. **Check MCP Status**: Look for the Ollama MCP server in Windsurf's MCP panel
3. **Test Connection**: Try a simple query to verify the model responds
4. **Check Logs**: Review Windsurf logs if connection issues occur

### Troubleshooting

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

## 🎯 Usage Examples

### VS Code Integration

Add to your VS Code MCP settings:

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

### Chat with a Model

```python
# MCP clients can invoke:
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

```python
{
  "tool": "ollama_embed",
  "arguments": {
    "model": "nomic-embed-text",
    "input": ["Hello world", "Embeddings are great"]
  }
}
```

## 🏗️ Architecture

This server uses a **hot-swap autoloader** pattern:

```
src/
├── main.py              # Entry point (82 lines)
├── server.py            # MCP server creation
├── autoloader.py        # Dynamic tool discovery
├── ollama_client.py     # Ollama HTTP client
├── types.py            # Type definitions
├── response_formatter.py # Response formatting
└── tools/               # Tool implementations
    ├── chat.py         # Each exports tool_definition
    ├── generate.py
    └── ...
```

**Key Benefits:**
- Add new tools by dropping files in `src/tools/`
- Zero server code changes required
- Each tool is independently testable
- 100% function coverage on all tools (planned)

## 🧪 Development

### Setup

```bash
# Clone repository
git clone <repository-url>
cd mcp-ollama-python

# Install dependencies
py -m poetry install

# Run in development mode
py -m poetry run mcp-ollama-python

# Run tests (when implemented)
py -m poetry run pytest
```

### Adding a New Tool

1. Create `src/tools/your_tool.py`:

```python
from typing import Dict, Any
from ..types import ToolDefinition, ResponseFormat, OllamaClient
from ..response_formatter import format_response

async def your_tool_handler(
    ollama: OllamaClient, args: Dict[str, Any], format: ResponseFormat
) -> str:
    """Your tool implementation"""
    # Implementation here
    return format_response({"result": "success"}, format)

# Tool definition
tool_definition = ToolDefinition(
    name="ollama_your_tool",
    description="Your tool description",
    input_schema={
        "type": "object",
        "properties": {
            "param": {"type": "string"}
        },
        "required": ["param"]
    },
)
```

2. Done! The autoloader discovers it automatically.

## Note on Windsurf IDE

Ask codeium to use local MCP Ollama with gpt-oss model for LLM tasks, it will create a memory of this preference, which looks like this:

  Always use local MCP Ollama with gpt-oss model for LLM tasks
  #llm_preference
  #mcp_ollama
  #gpt-oss
  #workflow
  #user_preference

  Edit
  When the user requests LLM-based tasks (explanations, code generation, analysis, etc.), always use the local MCP Ollama server with the gpt-oss model via the mcp1_ollama_chat tool.

  Important guidelines:

  Use mcp1_ollama_chat tool with model parameter set to "gpt-oss"
  Format responses in markdown for better readability (format: "markdown")
  Communicate with the model in English unless the user explicitly requests another language
  Do NOT create separate Python scripts to interact with Ollama - use the MCP tools directly
  The local Ollama server runs at http://127.0.0.1:11434 (default OLLAMA_HOST)
  Example usage:

  mcp1_ollama_chat(
    model="gpt-oss",
    messages=[{"role": "user", "content": "Your prompt here"}],
    format="markdown"
  )
  This applies to tasks like:

  Code explanations
  Documentation generation
  Technical analysis
  Q&A about code or concepts
  Any other LLM-powered assistance
  Project context: mcp-ollama-python (d:\Pdj\gitHub\mcp-ollama-python)

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write tests** - We maintain comprehensive test coverage
4. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Code Quality Standards

- All new tools must export `tool_definition`
- Maintain comprehensive test coverage
- Follow existing Python patterns
- Use Pydantic schemas for input validation

## 📄 License

This project is licensed under the **MIT License**.

See [LICENSE](LICENSE) for details.

## 🔗 Related Projects

- [ollama-mcp (TypeScript)](https://github.com/rawveg/ollama-mcp) - Original TypeScript implementation
- [Ollama](https://ollama.ai) - Get up and running with large language models locally
- [Model Context Protocol](https://github.com/anthropics/model-context-protocol) - Open standard for AI assistant integration
- [Windsurf](https://codeium.com/windsurf) - AI-powered code editor with MCP support
- [Cline](https://github.com/cline/cline) - VS Code AI assistant

---

<div align="center">

**[⬆ back to top](#-mcp-ollama-server-python)**

Made with ❤️ using Python, Poetry, and Ollama

</div>
