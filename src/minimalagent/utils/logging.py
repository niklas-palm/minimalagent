"""Logging utilities for MinimalAgent."""

# Standard library imports
import logging
import sys
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


def setup_logging(
    show_reasoning: bool = True, log_level: str = "WARNING"
) -> logging.Logger:
    """
    Configure logging system for the agent.

    Args:
        show_reasoning: Whether to show agent's step-by-step reasoning process with colors
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        The configured agent logger
    """
    # Set the general logging level based on the log_level parameter
    try:
        level = getattr(logging, log_level.upper())
    except AttributeError:
        level = logging.WARNING  # Default to WARNING if invalid level provided
        print(f"Warning: Invalid log level '{log_level}'. Using WARNING level instead.")

    # Configure the standard logger
    logger.setLevel(level)

    # Prevent propagation to parent loggers to avoid duplicate logs
    logger.propagate = False

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a standard handler for normal logging
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)

    # Create a formatter for normal logs
    standard_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(standard_formatter)

    # Add our handler
    logger.addHandler(console_handler)

    # Add reasoning display methods
    if show_reasoning:
        # Add display_ methods for colorized output
        logger.display_query = lambda msg: color_log(msg, Colors.BOLD + Colors.CYAN)
        logger.display_step = lambda msg: color_log(msg, Colors.BOLD + Colors.YELLOW)
        logger.display_thinking = lambda msg: print(msg)
        logger.display_action = lambda msg: color_log(msg, Colors.GREEN)
        logger.display_tool = lambda msg: color_log(msg, Colors.BOLD + Colors.GREEN)
        logger.display_error = lambda msg: color_log(msg, Colors.RED)
        logger.display_final = lambda msg: color_log(msg, Colors.BOLD + Colors.GREEN)
        logger.display_delimiter = lambda: color_log("-" * 80, Colors.BLUE)
        logger.display_subdelimiter = lambda: color_log("-" * 40, Colors.YELLOW)
        logger.display_print = lambda msg: print(msg)
        logger.display_info = lambda msg: color_log(msg, Colors.BLUE)
    else:
        # Create no-op methods when reasoning display is disabled
        logger.display_query = lambda msg: None
        logger.display_step = lambda msg: None
        logger.display_thinking = lambda msg: None
        logger.display_action = lambda msg: None
        logger.display_tool = lambda msg: None
        logger.display_error = lambda msg: None
        logger.display_final = lambda msg: None
        logger.display_delimiter = lambda: None
        logger.display_subdelimiter = lambda: None
        logger.display_print = lambda msg: None
        logger.display_info = lambda msg: None

    return logger
