# Server Control Guide

This guide explains how to start, stop, and manage the Ollama MCP Server.

## Quick Start

### Method 1: Using the Control Script (Recommended)

The easiest way to manage the server:

```bash
# Start the server
python server_control.py start

# Check server status
python server_control.py status

# Stop the server
python server_control.py stop

# Restart the server
python server_control.py restart
```

### Method 2: Direct Execution

Run the server directly (blocks terminal):

```bash
# Using Poetry
py -m poetry run mcp-ollama-python

# Or directly with Python
python -m mcp_ollama_python

# Stop with Ctrl+C
```

### Method 3: Programmatic Control

Control the server from Python code:

```python
from mcp_ollama_python.main import run, stop
import threading

# Start server in background thread
server_thread = threading.Thread(target=run, daemon=True)
server_thread.start()

# ... do other work ...

# Stop the server
stop()
```

## Server Lifecycle

### Starting the Server

When you start the server, it will:
1. Initialize the Ollama client connection
2. Discover and load all tools from the `/tools` directory
3. Set up signal handlers for graceful shutdown
4. Start listening for MCP client connections via stdio

**Output:**
```
Starting Ollama MCP Server...
Press Ctrl+C to stop the server
Server started successfully!
Waiting for MCP client connections...
```

### Stopping the Server

The server supports graceful shutdown through multiple methods:

**Keyboard Interrupt (Ctrl+C):**
- Sends SIGINT signal
- Server completes current operations
- Closes Ollama client connections
- Cleans up resources

**Signal Termination:**
- SIGTERM signal for graceful shutdown
- Used by the control script and system managers

**Programmatic Stop:**
- Call `stop()` function from Python
- Sets shutdown event to trigger cleanup

### Server Status

Check if the server is running:

```bash
python server_control.py status
```

Output examples:
- `✓ Server is running (PID: 12345)`
- `✗ Server is not running`

## Integration with Windsurf

The server works seamlessly with Windsurf using stdio protocol.

**Windsurf Configuration:**

Add to your Windsurf MCP settings (`.windsurf/mcp_config.json`):

```json
{
  "mcpServers": {
    "ollama": {
      "command": "py",
      "args": ["-m", "poetry", "run", "mcp-ollama-python"],
      "cwd": "C:\myCode/gitHub/mcp-ollama-python"
    }
  }
}
```

**How it works:**
1. Windsurf launches the server as a subprocess
2. Server communicates via stdin/stdout
3. Windsurf sends MCP protocol messages
4. Server responds with tool results
5. When Windsurf closes, server shuts down automatically

## Troubleshooting

### Server Won't Start

**Check if already running:**
```bash
python server_control.py status
```

**Check Ollama connection:**
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags
```

**Check for port conflicts:**
The server uses stdio, not ports, so this shouldn't be an issue.

### Server Won't Stop

**Force stop:**
```bash
# Find the process
ps aux | grep mcp-ollama-python

# Kill it (replace PID)
kill -9 <PID>

# Or use the control script (includes force kill)
python server_control.py stop
```

### Clean Up Stale PID File

If the control script reports a running server but it's not actually running:

```bash
# Remove the PID file
rm .mcp_ollama_server.pid

# Or on Windows
del .mcp_ollama_server.pid
```

## Advanced Usage

### Running as a Service

**Linux (systemd):**

Create `/etc/systemd/system/mcp-ollama.service`:

```ini
[Unit]
Description=Ollama MCP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/mcp-ollama-python
ExecStart=/usr/bin/python3 -m mcp_ollama_python
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable mcp-ollama.service
sudo systemctl start mcp-ollama.service
sudo systemctl status mcp-ollama.service
```

**Windows (NSSM):**

```cmd
# Install NSSM (Non-Sucking Service Manager)
# Download from https://nssm.cc/

# Install service
nssm install OllamaMCP "C:\Python\python.exe" "-m mcp_ollama_python"
nssm set OllamaMCP AppDirectory "C:\myCode\gitHub\mcp-ollama-python"
nssm start OllamaMCP
```

### Custom Ollama Host

Set environment variable before starting:

```bash
# Linux/Mac
export OLLAMA_HOST="http://custom-host:11434"
python server_control.py start

# Windows
set OLLAMA_HOST=http://custom-host:11434
python server_control.py start
```

### Logging

Redirect output to log file:

```bash
# Start with logging
python -m mcp_ollama_python > server.log 2>&1 &

# View logs
tail -f server.log
```

## Server Signals

The server responds to the following signals:

- **SIGINT (Ctrl+C)**: Graceful shutdown
- **SIGTERM**: Graceful shutdown (used by system managers)
- **SIGKILL**: Force kill (not graceful, use as last resort)

## Exit Codes

- `0`: Success
- `1`: Error or server not running
- `130`: Interrupted by user (Ctrl+C)

## See Also

- [Home](index.md) - Main documentation
- [Architecture](architecture.md) - Server architecture details
- [Available Tools](tools.md) - List of MCP tools
