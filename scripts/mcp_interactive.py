#!/usr/bin/env python3
"""
Interactive MCP Server Management Script
Provides a menu-driven interface to manage and interact with the Ollama MCP Server
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import psutil

# Add src to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    from ollama_mcp_python.server import OllamaMCPServer
    from ollama_mcp_python.ollama_client import OllamaClient
    from ollama_mcp_python.models import ResponseFormat  # noqa: F401
except ImportError:
    print("Error: Could not import ollama_mcp_python modules")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Server process tracking (store in tmp directory)
TMP_DIR = PROJECT_ROOT / "tmp"
PID_FILE = TMP_DIR / ".ollama_mcp_server.pid"

# Environment variables storage (store in tmp directory)
ENV_VARS_FILE = TMP_DIR / ".mcp_env_vars.json"

# Server log files (store in logs directory)
LOGS_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOGS_DIR / "ollama_mcp_server.log"
ERROR_LOG_FILE = LOGS_DIR / "ollama_mcp_server_error.log"

# Ensure tmp and logs directories exist
TMP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


def is_mcp_server_process(pid: int) -> bool:
    """Check if the given PID corresponds to an actual MCP server process"""
    try:
        process = psutil.Process(pid)
        # Check if process is running and is a Python process
        if not process.is_running():
            return False

        # Check command line to verify it's the MCP server
        cmdline = process.cmdline()
        if not cmdline:
            return False

        # Look for Python executable and ollama_mcp_python module
        cmdline_str = ' '.join(cmdline).lower()

        # Check for various patterns that indicate this is our MCP server:
        # 1. Direct python -m ollama_mcp_python
        # 2. poetry run python -m ollama_mcp_python
        # 3. Any python process with ollama_mcp_python in the command line
        is_python = 'python' in cmdline_str or 'python.exe' in cmdline_str
        is_mcp = 'ollama_mcp_python' in cmdline_str or 'ollama-mcp-python' in cmdline_str

        # Also check if it's a poetry process that's running our module
        is_poetry_wrapper = 'poetry' in cmdline_str and is_mcp

        return (is_python and is_mcp) or is_poetry_wrapper
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def cleanup_stale_pipe_files(current_pid: Optional[int] = None):
    """Remove all pipe files that don't correspond to the running MCP server"""
    try:
        for pipe_file in TMP_DIR.glob(".ollama_mcp_server_*.pipe"):
            # Extract PID from filename
            try:
                filename = pipe_file.name
                pid_str = filename.replace(".ollama_mcp_server_", "").replace(".pipe", "")
                file_pid = int(pid_str)
                
                # Remove if it's not the current PID or if the process isn't running
                if file_pid != current_pid or not is_mcp_server_process(file_pid):
                    try:
                        pipe_file.unlink()
                    except OSError:
                        pass
            except (ValueError, OSError):
                # Invalid filename format, remove it
                try:
                    pipe_file.unlink()
                except OSError:
                    pass
    except OSError:
        pass


class MCPInteractive:
    """Interactive MCP Server Manager"""

    def __init__(self):
        self.env_vars = self.load_env_vars()
        self.server = None
        self.ollama_client = None

    def load_env_vars(self) -> Dict[str, str]:
        """Load saved environment variables"""
        if ENV_VARS_FILE.exists():
            try:
                return json.loads(ENV_VARS_FILE.read_text())
            except (json.JSONDecodeError, OSError):
                return {}
        return {}
    
    def save_env_vars(self):
        """Save environment variables to file"""
        ENV_VARS_FILE.write_text(json.dumps(self.env_vars, indent=2))
    
    def apply_env_vars(self):
        """Apply stored environment variables to current process"""
        for key, value in self.env_vars.items():
            os.environ[key] = value
    
    def get_server_pid(self) -> Optional[int]:
        """Get the PID of the running server if it exists and is valid"""
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                
                # Check if process exists and is actually the MCP server
                if is_mcp_server_process(pid):
                    # Clean up stale pipe files
                    cleanup_stale_pipe_files(current_pid=pid)
                    return pid
                else:
                    # Process doesn't exist or isn't the MCP server, clean up
                    PID_FILE.unlink()
                    cleanup_stale_pipe_files()
                    return None
            except (ValueError, FileNotFoundError):
                return None
        
        # No PID file, clean up any stale pipes
        cleanup_stale_pipe_files()
        return None
    
    def check_server_status(self):
        """Check and display server status"""
        print("\n" + "="*60)
        print("SERVER STATUS")
        print("="*60)
        
        pid = self.get_server_pid()
        if pid:
            print(f"✓ Server is RUNNING (PID: {pid})")
            print(f"  PID File: {PID_FILE}")
            
            # Debug: Show process details
            try:
                process = psutil.Process(pid)
                print(f"  Process: {process.name()}")
                print(f"  Command: {' '.join(process.cmdline()[:3])}...")
            except psutil.Error as e:
                print(f"  Debug error: {e}")
        else:
            print("✗ Server is NOT RUNNING")
            
            # Debug: Check if PID file exists but process check failed
            if PID_FILE.exists():
                try:
                    stored_pid = int(PID_FILE.read_text().strip())
                    print(f"  Debug: PID file exists with PID {stored_pid}")
                    try:
                        process = psutil.Process(stored_pid)
                        cmdline = ' '.join(process.cmdline())
                        print("  Debug: Process exists but validation failed")
                        print(f"  Debug: Command line: {cmdline}")
                    except psutil.NoSuchProcess:
                        print(f"  Debug: Process {stored_pid} does not exist")
                except (ValueError, OSError) as e:
                    print(f"  Debug: Error reading PID file: {e}")
        
        # Check Ollama connection
        print("\nOllama Connection:")
        ollama_host = os.environ.get('OLLAMA_HOST', 'http://127.0.0.1:11434')
        print(f"  Host: {ollama_host}")
        
        try:
            import httpx
            response = httpx.get(f"{ollama_host}/api/tags", timeout=2.0, follow_redirects=True)
            if response.status_code == 200:
                print("  Status: ✓ Connected")
                data = response.json()
                models = data.get('models', [])
                print(f"  Available Models: {len(models)}")
                if models:
                    print("  Models:", ", ".join([m['name'] for m in models[:5]]))
                    if len(models) > 5:
                        print(f"           ... and {len(models) - 5} more")
            else:
                print(f"  Status: ✗ Error (HTTP {response.status_code})")
        except httpx.RequestError as e:
            print(f"  Status: ✗ Cannot connect ({str(e)[:50]})")
        
        print("="*60)
        input("\nPress Enter to continue...")
    
    def start_server(self):
        """Start the MCP server"""
        print("\n" + "="*60)
        print("START SERVER")
        print("="*60)
        
        existing_pid = self.get_server_pid()
        if existing_pid:
            print("✗ Server is already running!")
            print(f"  PID: {existing_pid}")
            input("\nPress Enter to continue...")
            return
        
        print("\nCleaning up stale files...")
        cleanup_stale_pipe_files()
        
        print("Applying environment variables...")
        self.apply_env_vars()
        
        print("Starting Ollama MCP Server...")
        
        try:
            # Build command with environment variables
            env = os.environ.copy()
            env.update(self.env_vars)
            
            # Properly activate the virtual environment by setting all necessary env vars
            venv_path = PROJECT_ROOT / ".venv"
            venv_scripts = venv_path / "Scripts"
            
            # Set VIRTUAL_ENV to activate the venv
            env['VIRTUAL_ENV'] = str(venv_path)
            
            # Update PATH to prioritize venv Scripts directory
            env['PATH'] = f"{venv_scripts}{os.pathsep}{env.get('PATH', '')}"
            
            # Remove PYTHONHOME which can interfere with venv
            env.pop('PYTHONHOME', None)
            
            # Clear PYTHONPATH to prevent system paths from interfering with venv imports
            # This is critical - PYTHONPATH can cause import conflicts with venv packages
            if 'PYTHONPATH' in env:
                print(f"  Clearing PYTHONPATH: {env['PYTHONPATH']}")
                env.pop('PYTHONPATH', None)
            
            # Open log files
            log_file = open(LOG_FILE, 'w', encoding='utf-8')
            error_log_file = open(ERROR_LOG_FILE, 'w', encoding='utf-8')
            
            # Create a pipe for stdin to keep the server running
            # The server will wait for input on this pipe instead of exiting
            stdin_read, stdin_write = os.pipe()
            
            # Windows-specific: CREATE_NEW_PROCESS_GROUP to prevent Ctrl+C propagation
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            
            # Use the virtual environment's Python directly
            venv_python = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
            if not venv_python.exists():
                # Try Unix-style path
                venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
            
            if not venv_python.exists():
                print(f"✗ Virtual environment Python not found at {venv_python}")
                print("  Please ensure the virtual environment is set up correctly.")
                input("\nPress Enter to continue...")
                return
            
            print(f"  Using Python: {venv_python}")
            print(f"  Command: {venv_python} -m ollama_mcp_python")
            
            # Run the module directly without -I flag to ensure proper package imports
            process = subprocess.Popen(
                [str(venv_python), "-m", "ollama_mcp_python"],
                stdin=stdin_read,
                stdout=log_file,
                stderr=error_log_file,
                env=env,
                start_new_session=True,
                close_fds=False,
                creationflags=creationflags,
                cwd=PROJECT_ROOT
            )
            
            # Close the read end in parent process (child has it)
            os.close(stdin_read)
            # Keep the write end open to prevent EOF
            # Store it in tmp directory so we can close it when stopping the server
            pipe_file = TMP_DIR / f".ollama_mcp_server_{process.pid}.pipe"
            pipe_file.write_text(str(stdin_write))
            
            PID_FILE.write_text(str(process.pid))
            time.sleep(1)
            
            if process.poll() is None:
                print(f"\n✓ Server started successfully (PID: {process.pid})")
                print(f"  Log file: {LOG_FILE}")
                print(f"  Error log: {ERROR_LOG_FILE}")
            else:
                print("\n✗ Server failed to start")
                if ERROR_LOG_FILE.exists():
                    error_content = ERROR_LOG_FILE.read_text()
                    if error_content:
                        print(f"Error: {error_content[:500]}")
        except (OSError, subprocess.SubprocessError) as e:
            print(f"\n✗ Failed to start server: {e}")
        
        input("\nPress Enter to continue...")
    
    def stop_server(self):
        """Stop the running server"""
        print("\n" + "="*60)
        print("STOP SERVER")
        print("="*60)
        
        pid = self.get_server_pid()
        
        if not pid:
            print("✗ No server is currently running")
            input("\nPress Enter to continue...")
            return
        
        print(f"\nStopping server (PID: {pid})...")
        
        try:
            # Close the pipe to trigger server shutdown
            pipe_file = TMP_DIR / f".ollama_mcp_server_{pid}.pipe"
            if pipe_file.exists():
                try:
                    pipe_fd = int(pipe_file.read_text())
                    os.close(pipe_fd)
                    print("  Closed pipe file descriptor")
                except (ValueError, OSError):
                    pass
            
            # Send SIGTERM
            os.kill(pid, signal.SIGTERM)
            
            for _ in range(50):
                try:
                    os.kill(pid, 0)
                    time.sleep(0.1)
                except OSError:
                    break
            
            try:
                os.kill(pid, 0)
                print("  Server didn't stop gracefully, forcing shutdown...")
                # Windows doesn't have SIGKILL, use terminate via psutil
                try:
                    process = psutil.Process(pid)
                    if sys.platform == 'win32':
                        process.terminate()
                    else:
                        process.kill()  # Sends SIGKILL on Unix
                    process.wait(timeout=2)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            except OSError:
                pass
            
            # Clean up PID file and pipe files
            if PID_FILE.exists():
                PID_FILE.unlink()
            
            print("  Cleaning up temporary files...")
            cleanup_stale_pipe_files()
            
            print("\n✓ Server stopped successfully")
        except (OSError, psutil.Error) as e:
            print(f"\n✗ Failed to stop server: {e}")
            # Try to clean up anyway
            if PID_FILE.exists():
                PID_FILE.unlink()
            cleanup_stale_pipe_files()
        
        input("\nPress Enter to continue...")
    
    def list_commands(self):
        """List available MCP commands"""
        print("\n" + "="*60)
        print("AVAILABLE MCP COMMANDS")
        print("="*60)
        
        print("\nInitializing server to discover tools...")
        
        try:
            # Create temporary server instance to discover tools
            from ollama_mcp_python.autoloader import discover_tools_with_handlers
            
            async def get_tools():
                registry = await discover_tools_with_handlers()
                return registry.tools
            
            tools = asyncio.run(get_tools())
            
            print(f"\nFound {len(tools)} tools:\n")
            
            for i, tool in enumerate(tools, 1):
                print(f"{i}. {tool.name}")
                print(f"   Description: {tool.description}")
                
                # Show input schema
                if tool.input_schema and 'properties' in tool.input_schema:
                    props = tool.input_schema['properties']
                    required = tool.input_schema.get('required', [])
                    
                    print("   Arguments:")
                    for prop_name, prop_info in props.items():
                        req_marker = "*" if prop_name in required else " "
                        prop_type = prop_info.get('type', 'any')
                        prop_desc = prop_info.get('description', 'No description')
                        print(f"     {req_marker} {prop_name} ({prop_type}): {prop_desc}")
                
                print()
        
        except (ImportError, RuntimeError) as e:
            print(f"\n✗ Error discovering tools: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")
    
    def manage_env_vars(self):
        """Manage environment variables"""
        while True:
            print("\n" + "="*60)
            print("ENVIRONMENT VARIABLES MANAGEMENT")
            print("="*60)
            
            print("\n1. View current environment variables")
            print("2. Add/Update environment variable")
            print("3. Remove environment variable")
            print("4. Reset to defaults")
            print("5. Back to main menu")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                self.view_env_vars()
            elif choice == '2':
                self.add_env_var()
            elif choice == '3':
                self.remove_env_var()
            elif choice == '4':
                self.reset_env_vars()
            elif choice == '5':
                break
            else:
                print("Invalid option. Please try again.")
    
    def view_env_vars(self):
        """View current environment variables"""
        print("\n" + "-"*60)
        print("CURRENT ENVIRONMENT VARIABLES")
        print("-"*60)
        
        if not self.env_vars:
            print("\nNo custom environment variables set.")
            print("\nCommon variables you might want to set:")
            print("  OLLAMA_HOST - Ollama server URL (default: http://127.0.0.1:11434)")
            print("  OLLAMA_API_KEY - API key for Ollama (if required)")
            print("  OLLAMA_MODELS - Custom models directory")
        else:
            print()
            for key, value in self.env_vars.items():
                print(f"  {key} = {value}")
        
        # Show system environment variables related to Ollama
        print("\n" + "-"*60)
        print("SYSTEM ENVIRONMENT VARIABLES (Ollama-related)")
        print("-"*60)
        
        ollama_vars = {k: v for k, v in os.environ.items() if 'OLLAMA' in k.upper()}
        if ollama_vars:
            for key, value in ollama_vars.items():
                print(f"  {key} = {value}")
        else:
            print("\nNo Ollama-related system variables found.")
        
        input("\nPress Enter to continue...")
    
    def add_env_var(self):
        """Add or update an environment variable"""
        print("\n" + "-"*60)
        print("ADD/UPDATE ENVIRONMENT VARIABLE")
        print("-"*60)
        
        print("\nCommon variables:")
        print("  OLLAMA_HOST")
        print("  OLLAMA_API_KEY")
        print("  OLLAMA_MODELS")
        
        key = input("\nEnter variable name (or 'cancel' to go back): ").strip()
        
        if key.lower() == 'cancel':
            return
        
        if not key:
            print("Variable name cannot be empty.")
            input("\nPress Enter to continue...")
            return
        
        current = self.env_vars.get(key, os.environ.get(key, ''))
        if current:
            print(f"\nCurrent value: {current}")
        
        value = input(f"Enter value for {key}: ").strip()
        
        if value:
            self.env_vars[key] = value
            self.save_env_vars()
            print(f"\n✓ Set {key} = {value}")
        else:
            print("\nValue cannot be empty. Variable not updated.")
        
        input("\nPress Enter to continue...")
    
    def remove_env_var(self):
        """Remove an environment variable"""
        print("\n" + "-"*60)
        print("REMOVE ENVIRONMENT VARIABLE")
        print("-"*60)
        
        if not self.env_vars:
            print("\nNo custom environment variables to remove.")
            input("\nPress Enter to continue...")
            return
        
        print("\nCurrent variables:")
        for i, key in enumerate(self.env_vars.keys(), 1):
            print(f"  {i}. {key} = {self.env_vars[key]}")
        
        choice = input("\nEnter variable name or number to remove (or 'cancel'): ").strip()
        
        if choice.lower() == 'cancel':
            return
        
        # Try as number first
        try:
            idx = int(choice) - 1
            keys = list(self.env_vars.keys())
            if 0 <= idx < len(keys):
                key = keys[idx]
            else:
                print("Invalid number.")
                input("\nPress Enter to continue...")
                return
        except ValueError:
            key = choice
        
        if key in self.env_vars:
            del self.env_vars[key]
            self.save_env_vars()
            print(f"\n✓ Removed {key}")
        else:
            print(f"\n✗ Variable '{key}' not found.")
        
        input("\nPress Enter to continue...")
    
    def reset_env_vars(self):
        """Reset environment variables to defaults"""
        print("\n" + "-"*60)
        print("RESET ENVIRONMENT VARIABLES")
        print("-"*60)
        
        confirm = input("\nAre you sure you want to reset all custom variables? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            self.env_vars = {}
            self.save_env_vars()
            print("\n✓ All custom environment variables cleared.")
        else:
            print("\nReset cancelled.")
        
        input("\nPress Enter to continue...")
    
    def run_mcp_command(self):
        """Run an MCP command interactively"""
        print("\n" + "="*60)
        print("RUN MCP COMMAND")
        print("="*60)
        
        print("\nInitializing MCP server...")
        
        try:
            # Apply environment variables
            self.apply_env_vars()
            
            # Initialize server components
            async def execute_command():
                ollama_client = OllamaClient()
                server = OllamaMCPServer(ollama_client)
                
                # Get available tools
                tools_result = await server.handle_list_tools()
                tools = tools_result['tools']
                
                if not tools:
                    print("\n✗ No tools available.")
                    return
                
                # Display tools
                print(f"\nAvailable commands ({len(tools)}):\n")
                for i, tool in enumerate(tools, 1):
                    print(f"{i}. {tool['name']}")
                    print(f"   {tool['description']}")
                
                # Get user selection
                print()
                choice = input("Select command number (or 'cancel' to go back): ").strip()
                
                if choice.lower() == 'cancel':
                    return
                
                try:
                    idx = int(choice) - 1
                    if not (0 <= idx < len(tools)):
                        print("\n✗ Invalid selection.")
                        return
                except ValueError:
                    print("\n✗ Invalid input. Please enter a number.")
                    return
                
                selected_tool = tools[idx]
                tool_name = selected_tool['name']
                
                print("\n" + "-"*60)
                print(f"COMMAND: {tool_name}")
                print("-"*60)
                print(f"Description: {selected_tool['description']}")
                
                # Get arguments
                args = {}
                schema = selected_tool.get('inputSchema', {})
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                if properties:
                    print("\nArguments:")
                    for prop_name, prop_info in properties.items():
                        is_required = prop_name in required
                        prop_type = prop_info.get('type', 'string')
                        prop_desc = prop_info.get('description', '')
                        
                        req_marker = "[REQUIRED]" if is_required else "[OPTIONAL]"
                        print(f"\n  {prop_name} ({prop_type}) {req_marker}")
                        if prop_desc:
                            print(f"  {prop_desc}")
                        
                        # Handle different types
                        if prop_type == 'array':
                            # Special handling for chat messages
                            if prop_name == 'messages' and tool_name == 'ollama_chat':
                                value = input(f"  Enter your message: ").strip()
                                if value:
                                    # Format as chat message array
                                    args[prop_name] = [{"role": "user", "content": value}]
                                elif is_required:
                                    print(f"  ✗ {prop_name} is required!")
                                    return
                            else:
                                value = input("  Enter value (comma-separated for array): ").strip()
                                if value:
                                    args[prop_name] = [v.strip() for v in value.split(',')]
                                elif is_required:
                                    print(f"  ✗ {prop_name} is required!")
                                    return
                        elif prop_type == 'object':
                            value = input("  Enter value (JSON format): ").strip()
                            if value:
                                try:
                                    args[prop_name] = json.loads(value)
                                except json.JSONDecodeError:
                                    print("  ✗ Invalid JSON format!")
                                    return
                            elif is_required:
                                print(f"  ✗ {prop_name} is required!")
                                return
                        else:
                            value = input("  Enter value: ").strip()
                            if value:
                                args[prop_name] = value
                            elif is_required:
                                print(f"  ✗ {prop_name} is required!")
                                return
                
                # Ask for output format
                print("\nOutput format:")
                print("  1. JSON")
                print("  2. Markdown")
                format_choice = input("Select format (1 or 2, default: 1): ").strip() or "1"
                args['format'] = 'markdown' if format_choice == '2' else 'json'
                
                # Execute command
                print("\n" + "="*60)
                print("EXECUTING COMMAND...")
                print("="*60)
                
                result = await server.handle_call_tool(tool_name, args)
                
                print("\n" + "-"*60)
                print("RESULT:")
                print("-"*60)
                
                # Display result
                if 'content' in result:
                    for item in result['content']:
                        if item.get('type') == 'text':
                            print(item['text'])
                
                if result.get('isError'):
                    print("\n✗ Command execution failed.")
                else:
                    print("\n✓ Command executed successfully.")
                
                # Cleanup
                await ollama_client.client.aclose()
            
            asyncio.run(execute_command())
        
        except (RuntimeError, asyncio.CancelledError) as e:
            print(f"\n✗ Error executing command: {e}")
            import traceback
            traceback.print_exc()
        
        input("\nPress Enter to continue...")
    
    def view_logs(self):
        """View server logs"""
        print("\n" + "="*60)
        print("SERVER LOGS")
        print("="*60)
        
        if LOG_FILE.exists():
            print("\nLog file:")
            print(LOG_FILE)
            try:
                # Read with explicit encoding and handle potential encoding issues
                with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if content.strip():
                        print("\nLog content:")
                        print(content)
                    else:
                        print("\nLog file is empty.")
            except OSError as e:
                print(f"\nError reading log file: {e}")
        else:
            print("\nNo log file found.")
        
        if ERROR_LOG_FILE.exists():
            print("\n" + "-"*60)
            print("Error log file:")
            print(ERROR_LOG_FILE)
            try:
                with open(ERROR_LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                    if content.strip():
                        print("\nError log content:")
                        print(content)
                    else:
                        print("\nError log file is empty (no errors).")
            except OSError as e:
                print(f"\nError reading error log file: {e}")
        else:
            print("\nNo error log file found.")
        
        # Show file sizes for debugging
        print("\n" + "-"*60)
        print("File Information:")
        if LOG_FILE.exists():
            size = LOG_FILE.stat().st_size
            print(f"  Log file size: {size} bytes")
        if ERROR_LOG_FILE.exists():
            size = ERROR_LOG_FILE.stat().st_size
            print(f"  Error log file size: {size} bytes")
        
        input("\nPress Enter to continue...")
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*60)
        print("OLLAMA MCP SERVER - INTERACTIVE MANAGER")
        print("="*60)
        print("1. Check MCP server status")
        print("2. Start server")
        print("3. Stop server")
        print("4. View server logs")
        print("5. List server commands and arguments")
        print("6. Manage environment variables")
        print("7. View current environment variables")
        print("8. Run MCP command")
        print("9. Exit")
        print("\n" + "="*60)
    
    def run(self):
        """Main loop"""
        while True:
            self.show_menu()
            choice = input("\nSelect option (1-9): ").strip()
            
            if choice == '1':
                self.check_server_status()
            elif choice == '2':
                self.start_server()
            elif choice == '3':
                self.stop_server()
            elif choice == '4':
                self.view_logs()
            elif choice == '5':
                self.list_commands()
            elif choice == '6':
                self.manage_env_vars()
            elif choice == '7':
                self.view_env_vars()
            elif choice == '8':
                self.run_mcp_command()
            elif choice == '9':
                print("\nExiting... Goodbye!")
                break
            else:
                print("\nInvalid option. Please try again.")
                input("\nPress Enter to continue...")


def main():
    """Main entry point"""
    try:
        manager = MCPInteractive()
        manager.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except (RuntimeError, OSError) as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
