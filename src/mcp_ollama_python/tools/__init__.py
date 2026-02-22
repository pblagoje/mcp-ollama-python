"""
Ollama MCP Tools Package

This package contains tools for interacting with Ollama models via MCP protocol.
Tools are automatically discovered by the autoloader at runtime.
"""

import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

__all__ = ["__version__"]
__version__ = "0.1.0"
