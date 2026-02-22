"""
Entry point for running as: python -m mcp_ollama_python

This module serves as the command-line interface for the package.
"""

import logging
import sys
from typing import NoReturn

from .main import run

logger = logging.getLogger(__name__)


def main() -> NoReturn:
    """
    Main entry point for the package.

    Executes the run function with proper error handling for keyboard
    interrupts and unexpected exceptions.

    Raises:
        SystemExit: Always exits with code 0 on success or interrupt,
                   code 1 on error
    """
    try:
        run()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        logger.error("Unexpected error occurred: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
