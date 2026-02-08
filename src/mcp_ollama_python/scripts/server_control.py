#!/usr/bin/env python3
"""
Ollama MCP Server Control Script
Provides easy start/stop/status commands for the MCP server

Package-compatible version — uses ~/.mcp-ollama-python/ for data storage.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import psutil

# Data directory in user home
DATA_DIR = Path.home() / ".mcp-ollama-python"
TMP_DIR = DATA_DIR / "tmp"
PID_FILE = TMP_DIR / ".mcp_ollama_server.pid"


def _ensure_dirs():
    """Create data directories on first use (not at import time)."""
    TMP_DIR.mkdir(parents=True, exist_ok=True)


def is_mcp_server_process(pid: int) -> bool:
    """Check if the given PID corresponds to an actual MCP server process"""
    try:
        process = psutil.Process(pid)
        if not process.is_running():
            return False

        cmdline = process.cmdline()
        if not cmdline:
            return False

        cmdline_str = " ".join(cmdline).lower()
        return "python" in cmdline_str and "mcp_ollama_python" in cmdline_str
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False


def cleanup_stale_pipe_files(current_pid: Optional[int] = None):
    """Remove all pipe files that don't correspond to the running MCP server"""
    try:
        for pipe_file in TMP_DIR.glob(".mcp_ollama_server_*.pipe"):
            try:
                filename = pipe_file.name
                pid_str = filename.replace(".mcp_ollama_server_", "").replace(
                    ".pipe", ""
                )
                file_pid = int(pid_str)

                if file_pid != current_pid or not is_mcp_server_process(file_pid):
                    try:
                        pipe_file.unlink()
                        print(f"  Cleaned up stale pipe file: {pipe_file.name}")
                    except OSError as e:
                        print(f"  Warning: Could not remove {pipe_file.name}: {e}")
            except (ValueError, OSError):
                try:
                    pipe_file.unlink()
                    print(f"  Cleaned up invalid pipe file: {pipe_file.name}")
                except OSError:
                    pass
    except OSError as e:
        print(f"  Warning: Error during pipe cleanup: {e}")


def get_server_pid() -> Optional[int]:
    """Get the PID of the running server if it exists and is valid"""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())

            if is_mcp_server_process(pid):
                cleanup_stale_pipe_files(current_pid=pid)
                return pid
            else:
                print("  Found stale PID file, cleaning up...")
                PID_FILE.unlink()
                cleanup_stale_pipe_files()
                return None
        except (ValueError, FileNotFoundError):
            return None

    cleanup_stale_pipe_files()
    return None


def start_server():
    """Start the MCP server"""
    existing_pid = get_server_pid()
    if existing_pid:
        print("Server is already running!")
        print(f"PID: {existing_pid}")
        return 1

    print("Starting Ollama MCP Server...")
    print("  Cleaning up stale files...")
    cleanup_stale_pipe_files()

    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_ollama_python"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )

        PID_FILE.write_text(str(process.pid))

        time.sleep(1)

        if process.poll() is None:
            print(f"✓ Server started successfully (PID: {process.pid})")
            print(f"  PID file: {PID_FILE}")
            print("Use 'mcp-server-control stop' to stop the server")
            return 0
        else:
            _, stderr = process.communicate()
            print("✗ Server failed to start")
            if stderr:
                print(f"Error: {stderr.decode()}")
            if PID_FILE.exists():
                PID_FILE.unlink()
            return 1

    except (OSError, subprocess.SubprocessError) as e:
        print(f"✗ Failed to start server: {e}")
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
        # Remove the pipe file to signal EOF to the child process.
        # Note: the numeric FD stored in the file is only valid in the
        # process that created it, so we just delete the file here.
        pipe_file = TMP_DIR / f".mcp_ollama_server_{pid}.pipe"
        if pipe_file.exists():
            try:
                pipe_file.unlink()
                print("  Removed pipe file")
            except OSError:
                pass

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
            try:
                process = psutil.Process(pid)
                if sys.platform == "win32":
                    process.terminate()
                else:
                    process.kill()  # Sends SIGKILL on Unix
                process.wait(timeout=2)
            except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                pass
        except OSError:
            pass

        if PID_FILE.exists():
            PID_FILE.unlink()

        print("  Cleaning up temporary files...")
        cleanup_stale_pipe_files()

        print("✓ Server stopped successfully")
        return 0

    except (OSError, psutil.Error) as e:
        print(f"✗ Failed to stop server: {e}")
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
    print(
        """
Ollama MCP Server Control

Usage:
    mcp-server-control [command]

Commands:
    start       Start the MCP server
    stop        Stop the running server
    restart     Restart the server
    status      Check if server is running
    help        Show this help message

Examples:
    mcp-server-control start
    mcp-server-control stop
    mcp-server-control status
"""
    )
    return 0


def main():
    """Main entry point"""
    _ensure_dirs()
    if len(sys.argv) < 2:
        show_help()
        return 1

    command = sys.argv[1].lower()

    commands = {
        "start": start_server,
        "stop": stop_server,
        "restart": restart_server,
        "status": server_status,
        "help": show_help,
    }

    if command in commands:
        return commands[command]()
    else:
        print(f"Unknown command: {command}")
        show_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
