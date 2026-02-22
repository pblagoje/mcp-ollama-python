#!/usr/bin/env python3
"""
Ollama MCP Server Control Script
Provides easy start/stop/status commands for the MCP server

Package-compatible version — uses ~/.mcp-ollama-python/ for data storage.
"""

import logging
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

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _ensure_dirs() -> None:
    """
    Create data directories on first use (not at import time).

    Raises:
        OSError: If directory creation fails
    """
    logger.debug("Ensuring data directories exist")
    try:
        TMP_DIR.mkdir(parents=True, exist_ok=True)
        # Set restrictive permissions on PID file directory
        os.chmod(TMP_DIR, 0o700)
        logger.debug("Data directories created successfully")
    except OSError as e:
        logger.error("Failed to create data directories: %s", e, exc_info=True)
        raise


def is_mcp_server_process(pid: int) -> bool:
    """
    Check if the given PID corresponds to an actual MCP server process.

    Args:
        pid: Process ID to check

    Returns:
        True if the PID is a valid MCP server process, False otherwise
    """
    if not isinstance(pid, int) or pid <= 0:
        logger.warning("Invalid PID: %s", pid)
        return False

    logger.debug("Checking if PID %d is MCP server process", pid)
    try:
        process = psutil.Process(pid)
        if not process.is_running():
            logger.debug("PID %d is not running", pid)
            return False

        cmdline = process.cmdline()
        if not cmdline:
            logger.debug("PID %d has no command line", pid)
            return False

        cmdline_str = " ".join(cmdline).lower()
        is_mcp = "python" in cmdline_str and "mcp_ollama_python" in cmdline_str
        logger.debug("PID %d is MCP server: %s", pid, is_mcp)
        return is_mcp
    except psutil.NoSuchProcess:
        logger.debug("PID %d does not exist", pid)
        return False
    except psutil.AccessDenied:
        logger.warning("Access denied when checking PID %d", pid)
        return False
    except psutil.ZombieProcess:
        logger.debug("PID %d is a zombie process", pid)
        return False


def cleanup_stale_pipe_files(current_pid: Optional[int] = None) -> None:
    """
    Remove all pipe files that don't correspond to the running MCP server.

    Args:
        current_pid: PID of the currently running server (if any)
    """
    logger.debug("Cleaning up stale pipe files (current_pid=%s)", current_pid)
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
                        logger.info("Cleaned up stale pipe file: %s", pipe_file.name)
                    except OSError as e:
                        logger.warning("Could not remove %s: %s", pipe_file.name, e)
            except ValueError as e:
                logger.debug("Invalid PID in pipe filename %s: %s", pipe_file.name, e)
                try:
                    pipe_file.unlink()
                    logger.info("Cleaned up invalid pipe file: %s", pipe_file.name)
                except OSError as e:
                    logger.warning(
                        "Could not remove invalid pipe file %s: %s", pipe_file.name, e
                    )
            except OSError as e:
                logger.warning("Error processing pipe file %s: %s", pipe_file.name, e)
    except OSError as e:
        logger.error("Error during pipe cleanup: %s", e, exc_info=True)


def get_server_pid() -> Optional[int]:
    """
    Get the PID of the running server if it exists and is valid.

    Returns:
        The PID of the running server, or None if not running
    """
    logger.debug("Getting server PID from %s", PID_FILE)
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            logger.debug("Found PID %d in PID file", pid)

            if is_mcp_server_process(pid):
                cleanup_stale_pipe_files(current_pid=pid)
                logger.debug("Server is running with PID %d", pid)
                return pid
            else:
                logger.info("Found stale PID file, cleaning up")
                PID_FILE.unlink()
                cleanup_stale_pipe_files()
                return None
        except ValueError as e:
            logger.warning("Invalid PID in file: %s", e)
            return None
        except FileNotFoundError:
            logger.debug("PID file disappeared during read")
            return None

    cleanup_stale_pipe_files()
    return None


def start_server() -> int:
    """
    Start the MCP server.

    Returns:
        0 on success, 1 on failure
    """
    logger.info("Starting MCP server")
    existing_pid = get_server_pid()
    if existing_pid:
        logger.warning("Server is already running with PID %d", existing_pid)
        print("Server is already running!")
        print(f"PID: {existing_pid}")
        return 1

    print("Starting Ollama MCP Server...")
    logger.info("Cleaning up stale files")
    print("  Cleaning up stale files...")
    cleanup_stale_pipe_files()

    try:
        logger.debug("Starting subprocess: %s -m mcp_ollama_python", sys.executable)
        process = subprocess.Popen(
            [sys.executable, "-m", "mcp_ollama_python"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )

        PID_FILE.write_text(str(process.pid))
        # Set restrictive permissions on PID file
        os.chmod(PID_FILE, 0o600)
        logger.debug("Wrote PID %d to %s", process.pid, PID_FILE)

        time.sleep(1)

        if process.poll() is None:
            logger.info("Server started successfully with PID %d", process.pid)
            print(f"✓ Server started successfully (PID: {process.pid})")
            print(f"  PID file: {PID_FILE}")
            print("Use 'mcp-server-control stop' to stop the server")
            return 0
        else:
            _, stderr = process.communicate()
            logger.error(
                "Server failed to start: %s",
                stderr.decode() if stderr else "Unknown error",
            )
            print("✗ Server failed to start")
            if stderr:
                print(f"Error: {stderr.decode()}")
            if PID_FILE.exists():
                PID_FILE.unlink()
            return 1

    except subprocess.SubprocessError as e:
        logger.error("Failed to start subprocess: %s", e, exc_info=True)
        print(f"✗ Failed to start server: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()
        return 1
    except OSError as e:
        logger.error("OS error during server start: %s", e, exc_info=True)
        print(f"✗ Failed to start server: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()
        return 1


def stop_server() -> int:
    """
    Stop the running server.

    Returns:
        0 on success, 1 on failure
    """
    logger.info("Stopping MCP server")
    pid = get_server_pid()

    if not pid:
        logger.warning("No server is currently running")
        print("No server is currently running")
        print("  Cleaning up stale files...")
        cleanup_stale_pipe_files()
        return 1

    logger.info("Stopping server with PID %d", pid)
    print(f"Stopping server (PID: {pid})...")

    try:
        # Remove the pipe file to signal EOF to the child process.
        pipe_file = TMP_DIR / f".mcp_ollama_server_{pid}.pipe"
        if pipe_file.exists():
            try:
                pipe_file.unlink()
                logger.debug("Removed pipe file for PID %d", pid)
                print("  Removed pipe file")
            except OSError as e:
                logger.warning("Could not remove pipe file: %s", e)

        logger.debug("Sending SIGTERM to PID %d", pid)
        os.kill(pid, signal.SIGTERM)

        # Wait for graceful shutdown (up to 5 seconds)
        for i in range(50):
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except OSError:
                logger.debug("Process stopped after %d iterations", i)
                break

        # Check if process is still running
        try:
            os.kill(pid, 0)
            logger.warning("Server didn't stop gracefully, forcing shutdown")
            print("  Server didn't stop gracefully, forcing shutdown...")
            try:
                process = psutil.Process(pid)
                if sys.platform == "win32":
                    process.terminate()
                else:
                    process.kill()  # Sends SIGKILL on Unix
                process.wait(timeout=2)
                logger.info("Forced shutdown successful")
            except psutil.NoSuchProcess:
                logger.debug("Process already terminated")
            except psutil.TimeoutExpired:
                logger.error("Process did not terminate after SIGKILL")
        except OSError:
            logger.debug("Process already stopped")

        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.debug("Removed PID file")

        logger.info("Cleaning up temporary files")
        print("  Cleaning up temporary files...")
        cleanup_stale_pipe_files()

        logger.info("Server stopped successfully")
        print("✓ Server stopped successfully")
        return 0

    except OSError as e:
        logger.error("OS error while stopping server: %s", e, exc_info=True)
        print(f"✗ Failed to stop server: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()
        cleanup_stale_pipe_files()
        return 1
    except psutil.Error as e:
        logger.error("psutil error while stopping server: %s", e, exc_info=True)
        print(f"✗ Failed to stop server: {e}")
        if PID_FILE.exists():
            PID_FILE.unlink()
        cleanup_stale_pipe_files()
        return 1


def restart_server() -> int:
    """
    Restart the server.

    Returns:
        0 on success, 1 on failure
    """
    logger.info("Restarting server")
    print("Restarting server...")
    stop_server()
    time.sleep(1)
    return start_server()


def server_status() -> int:
    """
    Check server status.

    Returns:
        0 if server is running, 1 if not running
    """
    logger.debug("Checking server status")
    pid = get_server_pid()

    if pid:
        logger.info("Server is running with PID %d", pid)
        print(f"✓ Server is running (PID: {pid})")
        return 0
    else:
        logger.info("Server is not running")
        print("✗ Server is not running")
        return 1


def show_help() -> int:
    """
    Show help message.

    Returns:
        Always returns 0
    """
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


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    logger.debug("Starting server control script")
    try:
        _ensure_dirs()
    except OSError as e:
        logger.error("Failed to initialize: %s", e)
        print(f"✗ Failed to initialize: {e}")
        return 1

    if len(sys.argv) < 2:
        show_help()
        return 1

    command = sys.argv[1].lower()
    logger.debug("Executing command: %s", command)

    commands = {
        "start": start_server,
        "stop": stop_server,
        "restart": restart_server,
        "status": server_status,
        "help": show_help,
    }

    if command in commands:
        try:
            return commands[command]()
        except Exception as e:
            logger.error("Command %s failed: %s", command, e, exc_info=True)
            print(f"✗ Command failed: {e}")
            return 1
    else:
        logger.warning("Unknown command: %s", command)
        print(f"Unknown command: {command}")
        show_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
