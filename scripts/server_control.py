#!/usr/bin/env python3
"""
Ollama MCP Server Control Script
Provides easy start/stop/status commands for the MCP server
"""

import subprocess
import sys
import os
import signal
import time
import psutil
from pathlib import Path
from typing import Optional

# Server process tracking (store in tmp directory)
PROJECT_ROOT = Path(__file__).parent.parent
TMP_DIR = PROJECT_ROOT / "tmp"
PID_FILE = TMP_DIR / ".ollama_mcp_server.pid"

# Ensure tmp directory exists
TMP_DIR.mkdir(exist_ok=True)


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
        
        # Look for Python executable and mcp_ollama_python module
        cmdline_str = ' '.join(cmdline).lower()
        return 'python' in cmdline_str and 'mcp_ollama_python' in cmdline_str
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
                        print(f"  Cleaned up stale pipe file: {pipe_file.name}")
                    except Exception as e:
                        print(f"  Warning: Could not remove {pipe_file.name}: {e}")
            except (ValueError, Exception):
                # Invalid filename format, remove it
                try:
                    pipe_file.unlink()
                    print(f"  Cleaned up invalid pipe file: {pipe_file.name}")
                except Exception:
                    pass
    except Exception as e:
        print(f"  Warning: Error during pipe cleanup: {e}")


def get_server_pid() -> Optional[int]:
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
                print("  Found stale PID file, cleaning up...")
                PID_FILE.unlink()
                cleanup_stale_pipe_files()
                return None
        except (ValueError, FileNotFoundError):
            return None
    
    # No PID file, clean up any stale pipes
    cleanup_stale_pipe_files()
    return None


def start_server():
    """Start the MCP server"""
    # Check if server is already running
    existing_pid = get_server_pid()
    if existing_pid:
        print("Server is already running!")
        print(f"PID: {existing_pid}")
        return 1
    
    print("Starting Ollama MCP Server...")
    print("  Cleaning up stale files...")
    cleanup_stale_pipe_files()
    
    # Start server as subprocess
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_ollama_python"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        # Save PID
        PID_FILE.write_text(str(process.pid))
        
        # Give it a moment to start
        time.sleep(1)
        
        # Check if it's still running
        if process.poll() is None:
            print(f"✓ Server started successfully (PID: {process.pid})")
            print(f"  PID file: {PID_FILE}")
            print("Use 'python server_control.py stop' to stop the server")
            return 0
        else:
            stdout, stderr = process.communicate()
            print(f"✗ Server failed to start")
            if stderr:
                print(f"Error: {stderr.decode()}")
            # Clean up PID file if start failed
            if PID_FILE.exists():
                PID_FILE.unlink()
            return 1
            
    except Exception as e:
        print(f"✗ Failed to start server: {e}")
        # Clean up PID file if start failed
        if PID_FILE.exists():
            PID_FILE.unlink()
        return 1


def stop_server():
    """Stop the running server"""
    pid = get_server_pid()
    
    if not pid:
        print("No server is currently running")
        print("  Cleaning up stale files...")
        cleanup_stale_pipe_files()
        return 1
    
    print(f"Stopping server (PID: {pid})...")
    
    try:
        # Close any associated pipe files
        pipe_file = TMP_DIR / f".ollama_mcp_server_{pid}.pipe"
        if pipe_file.exists():
            try:
                pipe_fd = int(pipe_file.read_text())
                os.close(pipe_fd)
                print("  Closed pipe file descriptor")
            except (ValueError, OSError):
                pass
        
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to stop (max 5 seconds)
        for _ in range(50):
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except OSError:
                # Process has stopped
                break
        
        # Check if still running
        try:
            os.kill(pid, 0)
            # Still running, force kill
            print("  Server didn't stop gracefully, forcing shutdown...")
            # Windows doesn't have SIGKILL, use SIGTERM or terminate via psutil
            if sys.platform == 'win32':
                try:
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=2)
                except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                    pass
            else:
                os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        
        # Clean up PID file and pipe files
        if PID_FILE.exists():
            PID_FILE.unlink()
        
        print("  Cleaning up temporary files...")
        cleanup_stale_pipe_files()
        
        print("✓ Server stopped successfully")
        return 0
        
    except Exception as e:
        print(f"✗ Failed to stop server: {e}")
        # Try to clean up anyway
        if PID_FILE.exists():
            PID_FILE.unlink()
        cleanup_stale_pipe_files()
        return 1


def restart_server():
    """Restart the server"""
    print("Restarting server...")
    stop_server()
    time.sleep(1)
    return start_server()


def server_status():
    """Check server status"""
    pid = get_server_pid()
    
    if pid:
        print(f"✓ Server is running (PID: {pid})")
        return 0
    else:
        print("✗ Server is not running")
        return 1


def show_help():
    """Show help message"""
    print("""
Ollama MCP Server Control

Usage:
    python server_control.py [command]

Commands:
    start       Start the MCP server
    stop        Stop the running server
    restart     Restart the server
    status      Check if server is running
    help        Show this help message

Examples:
    python server_control.py start
    python server_control.py stop
    python server_control.py status
""")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return 1
    
    command = sys.argv[1].lower()
    
    commands = {
        'start': start_server,
        'stop': stop_server,
        'restart': restart_server,
        'status': server_status,
        'help': show_help,
    }
    
    if command in commands:
        return commands[command]()
    else:
        print(f"Unknown command: {command}")
        show_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
