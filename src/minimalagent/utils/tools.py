"""Tool utilities for MinimalAgent."""

# Standard library imports
from typing import Any, Callable, Dict


def create_tool_spec(name: str, func: Callable) -> Dict[str, Any]:
    """
    Create tool specification from a decorated function.

    Args:
        name: Tool name
        func: Decorated function with @tool decorator

    Returns:
        Dict with tool specification in the format required by Bedrock API
    """
    # Get the tool specifications
    if not hasattr(func, "tool_spec"):
        raise ValueError(f"Function {func.__name__} must be decorated with @tool")

    spec = func.tool_spec

    # Build the tool parameters
    parameters = {"type": "object", "properties": {}, "required": spec["required"]}

    # Add properties to schema
    for prop_name, prop_spec in spec["properties"].items():
        parameters["properties"][prop_name] = prop_spec

    # Build the tool specification in the format expected by Bedrock API
    tool_spec = {
        "toolSpec": {
            "name": name,
            "description": spec["description"],
            "inputSchema": {"json": parameters},
        }
    }

    return tool_spec
