# MCP Interactive Manager Documentation

## Overview

`mcp_interactive.py` is an interactive menu-driven Python script that provides comprehensive management and interaction capabilities for the Ollama MCP (Model Context Protocol) Server. It offers a user-friendly terminal interface for server lifecycle management, command execution, environment configuration, and monitoring.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Main Menu Options](#main-menu-options)
- [File Structure](#file-structure)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Technical Details](#technical-details)
- [Troubleshooting](#troubleshooting)

## Features

### Core Capabilities

- **Server Lifecycle Management**: Start, stop, and monitor MCP server processes
- **Process Validation**: Intelligent PID file management with process verification using psutil
- **Environment Management**: Persistent environment variable configuration
- **Interactive Command Execution**: Execute MCP commands with guided parameter input
- **Real-time Monitoring**: Server status, Ollama connection, and available models display
- **Comprehensive Logging**: Separate log files for standard output and errors
- **Cross-Platform Support**: Windows and Unix/Linux compatibility
- **Automatic Cleanup**: Stale pipe file and PID file management

### Platform-Specific Features

- **Windows**: Uses `psutil.Process.terminate()` instead of SIGKILL for graceful shutdown
- **Unix/Linux**: Standard signal-based process management
- **Cross-platform**: Automatic detection and appropriate handling

## Prerequisites

### Software

| Tool | Minimum Version | Why it's needed |
|------|-----------------|------------------|
| **Python** | `3.10` or newer | Project code targets Python 3.10+. |
| **Poetry** | `>=1.6` | Handles the project's virtual environment and dependencies. |
| **Ollama** | Latest stable | Required for the `mcp_ollama_python` integration. |

> **Tip:** If you don't have Poetry installed, run  
> ```bash
> curl -sSL https://install.python-poetry.org | python3 -
> ```  
> or use your system package manager (e.g. `brew install poetry` on macOS, or `pip install poetry` on Windows).

### Python Packages

The project's dependencies are declared in `pyproject.toml`:

- `httpx >=0.27.0`
- `pydantic >=2.7.0`
- `rich >=13.7.0`
- `mcp >=1.0.0`
- `psutil >=7.1.3`

No `requirements.txt` is needed – Poetry takes care of resolving and pinning the exact versions.

## Installation

```bash
# 1. Clone the repository (if you haven't already)
git clone https://github.com/your-repo/mcp-ollama-python.git
cd mcp-ollama-python

# 2. (Optional) Verify that you are on the right Python version
python --version   # Should print 3.10.x or newer

# 3. Install the project's dependencies and create a virtual environment
poetry install

# 4. (Optional) Activate the virtual environment manually
poetry shell
#   • You'll now be inside the Poetry-managed venv and can run commands normally.

# 5. Verify Ollama is running
# Default: http://127.0.0.1:11434
# Or custom host via OLLAMA_HOST environment variable
```

### What `poetry install` does

1. **Creates** a fresh virtual environment (if one does not already exist).
2. **Installs** the exact dependency versions defined in `pyproject.toml`.
3. **Sets up** a `poetry.lock` file to guarantee reproducible installs.

> **NOTE:** The `poetry run` command automatically activates the environment for a single command, so you can skip `poetry shell` if you prefer a one-liner.

## Quick Start

### Running the Script

The recommended way to run the script is via Poetry. Choose one of the two approaches below:

**Option 1 – Run directly with Poetry**

```bash
poetry run python scripts/mcp_interactive.py
```

**Option 2 – Activate the Poetry shell first**

```bash
poetry shell
python scripts/mcp_interactive.py
```

Both commands start the virtual environment automatically and execute the `mcp_interactive.py` script from the `scripts` directory.

### Basic Workflow

1. **Check Status** (Option 1): Verify Ollama connection and available models
2. **Start Server** (Option 2): Launch the MCP server in the background
3. **Run Commands** (Option 8): Execute MCP tools interactively
4. **View Logs** (Option 4): Monitor server output and errors
5. **Stop Server** (Option 3): Gracefully shutdown the server

## Main Menu Options

The interactive menu provides 9 main options:

### 1. Check MCP Server Status

Displays comprehensive server and Ollama connection information:

- **Server Status**: Running/Not Running with PID
- **PID File Location**: Path to the PID file in `tmp/` directory
- **Ollama Connection**: Host URL and connection status
- **Available Models**: Count and list of first 5 models

**Example Output**:
```
============================================================
SERVER STATUS
============================================================
✓ Server is RUNNING (PID: 12345)
  PID File: D:\Pdj\gitHub\mcp-ollama-python\tmp\.mcp_ollama_server.pid

Ollama Connection:
  Host: http://127.0.0.1:11434
  Status: ✓ Connected
  Available Models: 21
  Models: llama3.1:latest, qwen3-vl:latest, glm4:latest, phi4:latest, llava:latest
           ... and 16 more
============================================================
```

### 2. Start Server

Launches the MCP server as a background process with:

- **Automatic Cleanup**: Removes stale pipe files before starting
- **Environment Variables**: Applies custom environment configuration
- **Logging**: Redirects stdout/stderr to log files
- **Process Isolation**: Uses subprocess with proper signal handling
- **PID Management**: Creates PID file for process tracking

**Features**:
- Prevents duplicate server instances
- Creates pipe file descriptors for graceful shutdown
- Windows-specific process group creation
- Automatic log file creation in `logs/` directory

### 3. Stop Server

Gracefully stops the running MCP server:

- **Pipe Closure**: Closes pipe file descriptors to signal shutdown
- **SIGTERM**: Sends termination signal for graceful exit
- **Force Shutdown**: Uses platform-specific force kill if needed (5-second timeout)
- **Cleanup**: Removes PID files and stale pipe files
- **Verification**: Confirms process termination

**Shutdown Process**:
1. Close pipe file descriptor
2. Send SIGTERM signal
3. Wait up to 5 seconds for graceful shutdown
4. Force terminate if still running (Windows: psutil, Unix: SIGKILL)
5. Clean up all temporary files

### 4. View Server Logs

Displays server log files with detailed information:

- **Standard Output Log**: `logs/mcp_ollama_server.log`
- **Error Log**: `logs/mcp_ollama_server_error.log`
- **File Sizes**: Shows log file sizes for debugging
- **UTF-8 Encoding**: Handles encoding issues gracefully

**Features**:
- Distinguishes between empty and missing log files
- Shows file paths for manual inspection
- Error handling for file read operations

### 5. List Server Commands and Arguments

Discovers and displays all available MCP tools:

- **Tool Discovery**: Uses autoloader to find all registered tools
- **Detailed Information**: Shows name, description, and arguments
- **Argument Details**: Displays type, requirement status, and descriptions
- **Schema Inspection**: Shows complete input schema for each tool

**Example Output**:
```
Found 8 tools:

1. ollama_list
   Description: List all available Ollama models
   Arguments:
     * format (string): Output format (default: json)

2. ollama_chat
   Description: Interactive chat with Ollama models
   Arguments:
     * model (string): Name of the model to use
     * messages (array): Array of chat messages
       format (string): Output format (default: json)
```

### 6. Manage Environment Variables

Submenu for comprehensive environment variable management:

**Sub-options**:
1. **View current environment variables**: Display custom and system variables
2. **Add/Update environment variable**: Set or modify variables
3. **Remove environment variable**: Delete custom variables
4. **Reset to defaults**: Clear all custom variables
5. **Back to main menu**: Return to main menu

**Common Variables**:
- `OLLAMA_HOST`: Ollama server URL (default: http://127.0.0.1:11434)
- `OLLAMA_API_KEY`: API key for Ollama (if required)
- `OLLAMA_MODELS`: Custom models directory

**Persistence**: Variables are saved to `tmp/.mcp_env_vars.json`

### 7. View Current Environment Variables

Displays environment configuration:

- **Custom Variables**: Variables set through the script
- **System Variables**: Ollama-related system environment variables
- **Suggestions**: Common variables you might want to set

### 8. Run MCP Command

Interactive command execution with guided parameter input:

**Workflow**:
1. **Tool Selection**: Choose from available MCP tools
2. **Parameter Input**: Guided prompts for each required/optional parameter
3. **Format Selection**: Choose JSON or Markdown output
4. **Execution**: Run the command with provided parameters
5. **Result Display**: Show formatted output

**Special Handling**:
- **Chat Messages**: Simplified input for chat message arrays
- **Arrays**: Comma-separated value input
- **Objects**: JSON format input with validation
- **Required vs Optional**: Clear indicators for parameter requirements

**Example Session**:
```
Available commands (8):

1. ollama_list
   List all available Ollama models

Select command number: 1

Arguments:
  format (string) [OPTIONAL]
  Output format (default: json)
  Enter value: json

Output format:
  1. JSON
  2. Markdown
Select format (1 or 2, default: 1): 1

============================================================
EXECUTING COMMAND...
============================================================

RESULT:
{
  "models": [...]
}

✓ Command executed successfully.
```

### 9. Exit

Cleanly exits the application.

## File Structure

The script manages files in organized directories:

```
mcp-ollama-python/
├── scripts/
│   └── mcp_interactive.py          # Main script
├── tmp/                             # Temporary files (auto-created)
│   ├── .mcp_ollama_server.pid      # Server process ID
│   ├── .mcp_ollama_server_*.pipe   # Pipe file descriptors
│   └── .mcp_env_vars.json          # Persistent environment variables
├── logs/                            # Log files (auto-created)
│   ├── mcp_ollama_server.log       # Standard output
│   └── mcp_ollama_server_error.log # Error output
└── src/
    └── mcp_ollama_python/           # MCP server package
```

### Directory Management

- **Automatic Creation**: `tmp/` and `logs/` directories are created automatically
- **Cleanup**: Stale pipe files are automatically removed
- **Persistence**: Environment variables persist across sessions

## Configuration

### Environment Variables

Set custom environment variables through the menu (Option 6) or directly in `tmp/.mcp_env_vars.json`:

```json
{
  "OLLAMA_HOST": "http://ai:11434/",
  "OLLAMA_API_KEY": "your-api-key-here"
}
```

### Default Configuration

- **Ollama Host**: `http://127.0.0.1:11434` (or `OLLAMA_HOST` env var)
- **Log Directory**: `logs/` (relative to project root)
- **Temp Directory**: `tmp/` (relative to project root)
- **Server Timeout**: 5 seconds for graceful shutdown

## Usage Examples

### Example 1: Start Server and Check Status

```bash
# Run the script
python mcp_interactive.py

# Select option 2 to start server
Select option (1-9): 2

# Wait for confirmation
✓ Server started successfully (PID: 12345)

# Select option 1 to check status
Select option (1-9): 1

# View status information
✓ Server is RUNNING (PID: 12345)
Ollama Connection: ✓ Connected
Available Models: 21
```

### Example 2: Configure Custom Ollama Host

```bash
# Select option 6 (Manage environment variables)
Select option (1-9): 6

# Select option 2 (Add/Update environment variable)
Select option (1-5): 2

# Enter variable name
Enter variable name: OLLAMA_HOST

# Enter value
Enter value for OLLAMA_HOST: http://ai:11434/

✓ Set OLLAMA_HOST = http://ai:11434/
```

### Example 3: Execute Chat Command

```bash
# Select option 8 (Run MCP command)
Select option (1-9): 8

# Select ollama_chat
Select command number: 2

# Enter model name
model (string) [REQUIRED]
Enter value: llava:latest

# Enter message
messages (array) [REQUIRED]
Enter your message: Explain what MCP is

# Select output format
Select format (1 or 2, default: 1): 2

# View result in Markdown format
RESULT:
MCP (Model Context Protocol) is a standardized protocol...

✓ Command executed successfully.
```

### Example 4: View Logs

```bash
# Select option 4 (View server logs)
Select option (1-9): 4

# View log content
Log file: D:\Pdj\gitHub\mcp-ollama-python\logs\mcp_ollama_server.log

Log content:
Starting Ollama MCP Server...
Server started successfully!
Waiting for MCP client connections...

File Information:
  Log file size: 156 bytes
  Error log file size: 0 bytes
```

## Technical Details

### Process Management

**PID Validation**:
- Uses `psutil.Process()` to verify process existence
- Checks command line for `mcp_ollama_python` to confirm identity
- Automatically cleans up stale PID files

**Process Creation**:
```python
# Windows-specific flags
creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

# Unix: start_new_session=True
process = subprocess.Popen(
    [sys.executable, "-m", "mcp_ollama_python"],
    stdin=stdin_read,
    stdout=log_file,
    stderr=error_log_file,
    start_new_session=True,
    creationflags=creationflags  # Windows only
)
```

### Pipe File Management

**Purpose**: Enable graceful server shutdown by closing stdin

**Implementation**:
1. Create pipe: `stdin_read, stdin_write = os.pipe()`
2. Pass read end to subprocess
3. Store write end in `tmp/.mcp_ollama_server_{pid}.pipe`
4. Close write end during shutdown to signal EOF

### Stale File Cleanup

**Automatic Cleanup**:
- Runs on server start, stop, and status check
- Removes pipe files for non-existent processes
- Removes pipe files for processes that aren't MCP servers
- Handles invalid filename formats gracefully

### Async Command Execution

**Architecture**:
```python
async def execute_command():
    ollama_client = OllamaClient()
    server = OllamaMCPServer(ollama_client)
    
    # Get tools and execute
    tools_result = await server.handle_list_tools()
    result = await server.handle_call_tool(tool_name, args)
    
    # Cleanup
    await ollama_client.client.aclose()

asyncio.run(execute_command())
```

### Cross-Platform Compatibility

**Windows**:
- Uses `psutil.Process.terminate()` for force shutdown
- Requires `CREATE_NEW_PROCESS_GROUP` flag
- No SIGKILL signal available

**Unix/Linux**:
- Uses `signal.SIGTERM` for graceful shutdown
- Uses `signal.SIGKILL` for force shutdown
- Standard signal handling

## Troubleshooting

### Common Issues

#### 1. Server Won't Start

**Symptoms**: Server fails to start, error in logs

**Solutions**:
- Check if Ollama is running: `curl http://localhost:11434/api/tags`
- Verify Python version: `python --version` (requires 3.10+)
- Ensure Poetry dependencies are installed: `poetry install`
- Check for port conflicts
- Review error log: `logs/mcp_ollama_server_error.log`
- Verify you're running with Poetry: `poetry run python scripts/mcp_interactive.py`

#### 2. Stale PID File

**Symptoms**: Script says server is running but it's not

**Solutions**:
- The script automatically detects and cleans stale PID files
- If issue persists, manually delete: `tmp/.mcp_ollama_server.pid`
- Run status check (Option 1) to trigger cleanup

#### 3. Cannot Connect to Ollama

**Symptoms**: "Cannot connect" error when checking status

**Solutions**:
- Verify Ollama is running: `ollama list`
- Check OLLAMA_HOST environment variable
- Test connection: `curl http://localhost:11434/api/tags`
- Configure custom host via Option 6

#### 4. Permission Denied on Windows

**Symptoms**: Cannot terminate process or delete files

**Solutions**:
- Run as Administrator
- Close any file handles to log files
- Wait a few seconds and try again
- Check antivirus software isn't blocking

#### 5. Logs Are Empty

**Symptoms**: Log files exist but contain no content

**Solutions**:
- Server may still be starting (wait a few seconds)
- Check file permissions on `logs/` directory
- Verify server is actually running (Option 1)
- Check error log for startup issues

#### 6. Command Execution Fails

**Symptoms**: MCP command returns error

**Solutions**:
- Verify model name is correct: Use Option 5 to list available tools
- Check required parameters are provided
- Ensure Ollama has the specified model: `ollama list`
- Review command syntax in tool description

#### 7. Poetry-Specific Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| **`poetry: command not found`** | Poetry is not installed or the binary is not on the PATH. | Install Poetry (e.g. `curl -sSL https://install.python-poetry.org | python3 -`) and add `~/.local/bin` (or the install prefix) to your `PATH`. Verify with `poetry --version`. |
| **Python version mismatch (`3.10+ required`)** | The current interpreter is older than the version required by the project. | Switch to a supported Python version (e.g., `pyenv install 3.12.0 && pyenv local 3.12.0`) or update the `python` key in `pyproject.toml` and re-run `poetry env use <python>`. |
| **`poetry.lock` conflicts or stale lock file** | The lock file was generated with a different Poetry version or after changes to dependencies. | Delete the lock file (`rm poetry.lock`), run `poetry lock` to regenerate it, and then `poetry install`. If the conflict is due to a specific dependency, adjust the version specifier in `pyproject.toml` before locking again. |
| **Virtual environment issues (env not created / missing packages)** | Poetry is unable to create or activate the virtual environment, often due to missing system packages or an incorrectly configured setting. | Ensure build tools are installed (`sudo apt install build-essential libffi-dev python3-dev` on Debian/Ubuntu, or Visual C++ Build Tools on Windows). If the env exists but is corrupted, delete it (`poetry env remove <name>`), then run `poetry install` to recreate. |

### Debug Mode

For detailed debugging:

1. **Check Process**: `ps aux | grep mcp_ollama_python` (Unix) or Task Manager (Windows)
2. **Manual Cleanup**: Delete files in `tmp/` directory
3. **View Raw Logs**: Open log files directly in text editor
4. **Test Ollama**: `curl http://localhost:11434/api/tags`

### Getting Help

If issues persist:

1. Check server logs (Option 4)
2. Verify Ollama connection (Option 1)
3. Review environment variables (Option 7)
4. Check GitHub issues for similar problems
5. Provide log files when reporting issues

## Advanced Usage

### Custom Ollama Host

For remote Ollama servers:

```bash
# Set via environment variable management (Option 6)
OLLAMA_HOST=http://remote-server:11434/
```

### Batch Operations

While the script is interactive, you can script operations:

```bash
# Start server programmatically
python -c "from mcp_interactive import MCPInteractive; m = MCPInteractive(); m.start_server()"
```

### Integration with Other Tools

The MCP server can be used by:
- Claude Desktop
- Cline VSCode Extension
- Custom MCP clients
- API integrations

## Security Considerations

- **API Keys**: Store sensitive keys in environment variables, not in code
- **Network Access**: Configure firewall rules for Ollama host
- **Process Isolation**: Server runs in separate process for security
- **Log Files**: May contain sensitive information, protect accordingly

## Performance Tips

- **Model Selection**: Smaller models respond faster
- **Log Rotation**: Periodically clear old log files
- **Resource Monitoring**: Check system resources if server is slow
- **Network Latency**: Use local Ollama instance for best performance

## License

This script is part of the mcp-ollama-python project. See the main project LICENSE file for details.

## Contributing

Contributions are welcome! Please see the main project CONTRIBUTING.md for guidelines.

---

**Last Updated**: December 2025  
**Version**: 1.0  
**Maintained By**: mcp-ollama-python contributors
