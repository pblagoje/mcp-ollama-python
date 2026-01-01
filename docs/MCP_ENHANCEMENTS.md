# MCP Ollama Server - Enhanced Capabilities

## Overview

The Ollama MCP server has been enhanced with full MCP protocol support including:
- ✅ **Resources** - Access to Ollama models, running processes, and configuration
- ✅ **Prompts** - Pre-built prompt templates for common tasks
- ✅ **Direct Execution** - Execute code with optional AI generation

## New Features

### 1. Resources Support

Resources provide read-only access to Ollama server information.

#### Available Resources

| URI | Name | Description |
|-----|------|-------------|
| `ollama://models` | Available Models | List of all available Ollama models |
| `ollama://running` | Running Models | List of currently running models |
| `ollama://config` | Ollama Configuration | Current Ollama server configuration |

#### Usage Example

```python
# List resources
from mcp1_ollama import list_resources
resources = list_resources("ollama")

# Read a resource
from mcp1_ollama import read_resource
config = read_resource("ollama", "ollama://config")
```

### 2. Prompts Support

Pre-built prompt templates for common AI tasks.

#### Available Prompts

| Name | Description | Arguments |
|------|-------------|-----------|
| `explain_lora` | Explain LoRA technique | `detail_level` (optional): basic, intermediate, advanced |
| `code_review` | Review code and provide feedback | `language` (required), `focus` (optional): security, performance, style, all |
| `hello_world` | Generate Hello World code | `language` (required) |

#### Usage Example

```python
# Via MCP tools
from mcp1_ollama_chat import chat

# Get prompt and use it
messages = [
    {"role": "user", "content": "Explain LoRA at a basic level"}
]

response = chat(
    model="llama3.1",
    messages=messages
)
```

### 3. Direct Code Execution

Execute code directly or generate and execute code using AI.

#### Execute Tool: `ollama_execute`

**Parameters:**
- `code` (string, optional): Code to execute
- `language` (string, default: "python"): Programming language
  - Supported: python, javascript, typescript, bash, shell, ruby, php, go
- `generate` (boolean, default: false): Generate code using AI before executing
- `prompt` (string, optional): Prompt for AI code generation (required if generate=true)
- `model` (string, default: "llama3.1"): Model to use for code generation
- `format` (string, default: "json"): Output format (json or markdown)

#### Usage Examples

**Example 1: Execute Provided Code**
```python
from mcp1_ollama_execute import execute

result = execute(
    code='print("Hello World")',
    language="python"
)
# Output: {"stdout": "Hello World\n", "returncode": 0, "success": true}
```

**Example 2: Generate and Execute Code**
```python
result = execute(
    generate=True,
    prompt="write hello world",
    language="python",
    model="llama3.1"
)
# AI generates code, then executes it
```

**Example 3: Generate Code in Different Languages**
```python
# JavaScript
result = execute(
    generate=True,
    prompt="print hello world to console",
    language="javascript"
)

# Bash
result = execute(
    generate=True,
    prompt="echo hello world",
    language="bash"
)
```

## Integration with Existing Tools

### Using Prompts with Chat

```python
from mcp1_ollama_chat import chat

# Use the explain_lora prompt
response = chat(
    model="llama3.1",
    messages=[
        {
            "role": "user", 
            "content": "Explain LoRA (Low-Rank Adaptation) at a basic level. Include: What it is and why it's useful, How it works technically, Use cases and benefits, Comparison with full fine-tuning"
        }
    ]
)
```

### Using Resources for Model Information

```python
from mcp1_ollama import read_resource
import json

# Get available models
models_json = read_resource("ollama", "ollama://models")
models = json.loads(models_json)

# Get running models
running_json = read_resource("ollama", "ollama://running")
running = json.loads(running_json)
```

## Architecture Changes

### Server Enhancements (`server.py`)

1. **Added Resource Management**
   - `_initialize_default_resources()`: Initialize resource registry
   - `handle_list_resources()`: List available resources
   - `handle_read_resource(uri)`: Read resource content

2. **Added Prompt Management**
   - `_initialize_default_prompts()`: Initialize prompt templates
   - `handle_list_prompts()`: List available prompts
   - `handle_get_prompt(name, arguments)`: Get prompt with arguments

### Main Entry Point (`main.py`)

Added MCP protocol handlers:
- `@mcp_server.list_resources()`: Resource listing handler
- `@mcp_server.read_resource()`: Resource reading handler
- `@mcp_server.list_prompts()`: Prompt listing handler
- `@mcp_server.get_prompt()`: Prompt retrieval handler

### New Tool (`tools/execute.py`)

Direct code execution tool with:
- AI-powered code generation
- Multi-language support
- Secure execution with timeouts
- Automatic cleanup of temporary files

## Security Considerations

### Code Execution Safety

1. **Timeout Protection**: All executions have a 30-second timeout
2. **Isolated Execution**: Code runs in subprocess isolation
3. **Temporary Files**: Automatic cleanup of temporary files
4. **No Shell Injection**: Proper command construction prevents injection

### Best Practices

- Only execute trusted code
- Review AI-generated code before execution
- Use appropriate language interpreters
- Monitor execution output for errors

## Testing

Run the test suite to verify all capabilities:

```bash
python test_mcp_capabilities.py
```

This will test:
- Resource listing and reading
- Prompt listing and retrieval
- Code execution (provided and generated)
- Integration with chat

## Example Use Cases

### 1. Explain Technical Concepts
```python
# Use the explain_lora prompt
response = chat(
    model="llama3.1",
    messages=[{"role": "user", "content": "Explain LoRA at an advanced level"}]
)
```

### 2. Generate and Run Code
```python
# Generate Hello World in any language
result = execute(
    generate=True,
    prompt="hello world program with comments",
    language="python"
)
```

### 3. Code Review
```python
# Use code_review prompt
response = chat(
    model="llama3.1",
    messages=[{
        "role": "user",
        "content": "Review the following Python code with focus on security..."
    }]
)
```

### 4. Monitor Ollama Server
```python
# Check running models
running = read_resource("ollama", "ollama://running")

# Check available models
models = read_resource("ollama", "ollama://models")
```

## Troubleshooting

### Resources Not Available
- Ensure Ollama server is running
- Check connection to `http://localhost:11434`
- Verify MCP server is properly initialized

### Code Execution Fails
- Verify language interpreter is installed (python, node, etc.)
- Check code syntax
- Review execution timeout (30 seconds)
- Examine stderr output for errors

### Prompt Not Found
- List available prompts with `list_prompts()`
- Verify prompt name spelling
- Check required arguments are provided

## Future Enhancements

Potential additions:
- More prompt templates (debugging, optimization, testing)
- Additional resources (model details, system metrics)
- Streaming execution output
- Multi-file code execution
- Custom resource registration
- Prompt template customization

## Summary

The enhanced MCP Ollama server now provides:
- **Full MCP Protocol Support**: Resources, Prompts, and Tools
- **Direct Execution**: Run code with AI assistance
- **Pre-built Prompts**: Common AI tasks ready to use
- **Server Monitoring**: Access to Ollama server information

This makes the Ollama MCP server a complete AI development platform with code generation, execution, and monitoring capabilities.
