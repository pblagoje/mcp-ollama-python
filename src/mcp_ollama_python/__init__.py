"""
Package initialization for mcp_ollama_python.

This module provides the main entry point and package-level exports.
"""

import logging

from .main import run

__all__ = ["run"]
__version__ = "0.1.0"

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
