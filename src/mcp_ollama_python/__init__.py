"""
Package initialization for mcp_ollama_python.

This module provides the main entry point and package-level exports.
"""

import logging
from importlib.metadata import version

from .main import run

__all__ = ["run", "__version__"]
__version__ = version("mcp-ollama-python")

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
