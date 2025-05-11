"""Logging utilities for MinimalAgent."""

# Standard library imports
import logging
from typing import Optional

# Configure agent logger
logger = logging.getLogger("minimalagent")


# ANSI color codes
class Colors:
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


def clean_log(message: str) -> None:
    """
    Print a clean log message without any formatting.

    Args:
        message: The message to print
    """
    print(message)


def color_log(message: str, color: Optional[str] = None) -> None:
    """
    Print a colored log message with ANSI formatting.

    Args:
        message: The message to print
        color: Optional ANSI color code from Colors class
    """
    if color:
        print(f"{color}{message}{Colors.END}")
    else:
        print(message)


def setup_logging(show_reasoning: bool = True) -> logging.Logger:
    """
    Configure logging system for the agent.

    Args:
        show_reasoning: Whether to show agent's step-by-step reasoning process

    Returns:
        The configured agent logger
    """
    # Configure our own logger
    logger.setLevel(logging.INFO if show_reasoning else logging.WARNING)

    # Override logger methods for color support if reasoning is shown
    if show_reasoning:
        logger.info = clean_log
        logger.error = lambda msg: color_log(msg, Colors.RED)

    return logger
