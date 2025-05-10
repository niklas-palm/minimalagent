"""Tests for the tool decorator."""

# Standard library imports
import pytest

# Project imports
from minimalagent import tool


def test_tool_decorator_basic():
    """Test basic tool decorator functionality."""

    @tool()
    def sample_tool():
        """Sample tool for testing."""
        return {"result": "success"}

    # Check that tool has spec
    assert hasattr(sample_tool, "tool_spec")

    # Check name default
    assert sample_tool.tool_spec["name"] == "sample_tool"

    # Check description default
    assert "Sample tool for testing" in sample_tool.tool_spec["description"]

    # Check no parameters
    assert sample_tool.tool_spec["properties"] == {}
    assert sample_tool.tool_spec["required"] == []


def test_tool_decorator_with_params():
    """Test tool decorator with parameters."""

    @tool(name="custom_name", description="Custom description")
    def sample_tool(required_param: str, optional_param: int = 0):
        """This docstring should be ignored."""
        return {"result": required_param}

    # Check name and description are customized
    assert sample_tool.tool_spec["name"] == "custom_name"
    assert sample_tool.tool_spec["description"] == "Custom description"

    # Check parameters are detected
    assert "required_param" in sample_tool.tool_spec["properties"]
    assert "optional_param" in sample_tool.tool_spec["properties"]

    # Check parameter types
    assert sample_tool.tool_spec["properties"]["required_param"]["type"] == "string"
    assert sample_tool.tool_spec["properties"]["optional_param"]["type"] == "integer"

    # Check required parameters
    assert "required_param" in sample_tool.tool_spec["required"]
    assert "optional_param" not in sample_tool.tool_spec["required"]
