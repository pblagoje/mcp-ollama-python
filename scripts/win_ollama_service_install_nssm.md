# Ollama Windows Service Installation

## Issue with Original Script

The original `win_ollama_service_install.ps1` script fails because **ollama.exe does not implement the Windows Service Control Manager (SCM) interface**. When you try to run it as a native Windows service, it times out after 30 seconds because it cannot communicate with the SCM.

**Error:** `Service 'ollama (ollama)' cannot be started due to the following error: Cannot start service ollama on computer '.'`

**Event Log Error:** `%%1053 - The service did not respond to the start or control request in a timely fashion`

## Solution: Use NSSM (Non-Sucking Service Manager)

NSSM is a service wrapper that allows any executable to run as a Windows service. It handles all the SCM communication.

## Installation

### Option 1: Automatic NSSM Download (Recommended)

Run the new script with automatic NSSM download:

```powershell
# Run as Administrator
.\win_ollama_service_install_nssm.ps1
```

The script will automatically:
- Download NSSM if not present
- Detect your Ollama installation
- Create and start the service
- Configure firewall rules

### Option 2: Manual NSSM Installation

1. Download NSSM from https://nssm.cc/download
2. Extract `nssm.exe` to the `scripts` folder
3. Run the installation script:

```powershell
# Run as Administrator
.\win_ollama_service_install_nssm.ps1
```

## Usage

### Install with Custom Options

```powershell
# Custom port
.\win_ollama_service_install_nssm.ps1 -Port 8080

# Custom model path
.\win_ollama_service_install_nssm.ps1 -ModelPath "D:\OllamaModels"

# Custom Ollama path
.\win_ollama_service_install_nssm.ps1 -OllamaPath "C:\Custom\Path\ollama.exe"

# All options combined
.\win_ollama_service_install_nssm.ps1 -Port 8080 -ModelPath "D:\OllamaModels" -ServiceName "ollama-custom"
```

### Manage the Service

```powershell
# Check status
Get-Service ollama

# Start service
Start-Service ollama

# Stop service
Stop-Service ollama

# Restart service
Restart-Service ollama
```

### View Logs

Service logs are stored in `scripts\logs\`:
- `ollama-stdout.log` - Standard output
- `ollama-stderr.log` - Error output

```powershell
# View recent logs
Get-Content .\logs\ollama-stdout.log -Tail 50
Get-Content .\logs\ollama-stderr.log -Tail 50
```

### Uninstall

```powershell
# Run as Administrator
.\win_ollama_service_install_nssm.ps1 -Uninstall
```

## How It Works

1. **NSSM wraps ollama.exe** - NSSM runs as the actual Windows service and manages the ollama.exe process
2. **Environment variables** - The script configures `OLLAMA_HOST` and optionally `OLLAMA_MODELS`
3. **Automatic restart** - If ollama crashes, NSSM automatically restarts it
4. **Log rotation** - Logs are automatically rotated when they reach 1MB

## Troubleshooting

### Service won't start

Check the error logs:
```powershell
Get-Content .\logs\ollama-stderr.log -Tail 50
```

### Port already in use

Stop any existing Ollama processes:
```powershell
Get-Process ollama | Stop-Process -Force
```

Then restart the service:
```powershell
Restart-Service ollama
```

### Check if Ollama is responding

```powershell
# Test the API
Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -Method GET
```

## Comparison: Native Service vs NSSM

| Feature | Native Windows Service | NSSM Wrapper |
|---------|----------------------|--------------|
| Works with ollama.exe | ❌ No (times out) | ✅ Yes |
| Auto-restart on crash | ⚠️ Limited | ✅ Full support |
| Log management | ❌ Manual | ✅ Automatic rotation |
| Easy configuration | ⚠️ Complex | ✅ Simple |
| Environment variables | ⚠️ Registry edits | ✅ Built-in |

## Additional Resources

- NSSM Documentation: https://nssm.cc/usage
- Ollama Documentation: https://github.com/ollama/ollama
