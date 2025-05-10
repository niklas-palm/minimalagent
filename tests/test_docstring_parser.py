"""Tests for docstring parsing functionality."""

# Standard library imports
import pytest

# Project imports
from minimalagent import tool
from minimalagent.utils.docstring import DocstringParser


def test_simple_docstring_parsing():
    """Test parsing a simple docstring."""

    def example_func():
        """This is a short description.

        This is a longer description that spans
        multiple lines and explains more details.

        Args:
            param1: First parameter
            param2: Second parameter with longer
                description that continues on the next line

        Returns:
            A string result
        """
        pass

    short_desc, long_desc, params = DocstringParser.parse(example_func)

    assert short_desc == "This is a short description."
    assert "multiple lines" in long_desc
    assert "param1" in params
    assert "param2" in params
    assert "continues on the next line" in params["param2"]


def test_docstring_without_args():
    """Test parsing a docstring with no Args section."""

    def example_func():
        """Just a short description."""
        pass

    short_desc, long_desc, params = DocstringParser.parse(example_func)

    assert short_desc == "Just a short description."
    assert long_desc == ""
    assert params == {}


def test_docstring_with_empty_args():
    """Test parsing a docstring with empty Args section."""

    def example_func():
        """Short description.

        Args:

        Returns:
            Nothing
        """
        pass

    short_desc, long_desc, params = DocstringParser.parse(example_func)

    assert short_desc == "Short description."
    assert params == {}


def test_tool_decorator_with_docstring():
    """Test tool decorator with docstring-based parsing."""

    @tool
    def weather_tool(location: str, units: str = "metric") -> dict:
        """Get weather for a location.

        Args:
            location: The location to get weather for
            units: Temperature units (metric or imperial)

        Returns:
            Weather data
        """
        return {"result": f"{location} weather"}

    # Check basic tool attributes
    assert weather_tool.tool_spec["name"] == "weather_tool"
    assert "Get weather for a location" in weather_tool.tool_spec["description"]

    # Check parameter properties
    assert "location" in weather_tool.tool_spec["properties"]
    assert "units" in weather_tool.tool_spec["properties"]

    # Check parameter descriptions were extracted from docstring
    assert (
        "The location to get"
        in weather_tool.tool_spec["properties"]["location"]["description"]
    )
    assert (
        "Temperature units"
        in weather_tool.tool_spec["properties"]["units"]["description"]
    )

    # Check required parameters
    assert "location" in weather_tool.tool_spec["required"]
    assert "units" not in weather_tool.tool_spec["required"]


def test_tool_decorator_with_parameter_override():
    """Test tool decorator with parameter description overrides."""

    @tool(param_descriptions={"param1": "Overridden description"})
    def custom_tool(param1: str, param2: int = 0) -> dict:
        """A custom tool.

        Args:
            param1: Original description
            param2: Second parameter

        Returns:
            Custom result
        """
        return {"result": "success"}

    # Check parameter description was overridden
    assert (
        "Overridden description"
        in custom_tool.tool_spec["properties"]["param1"]["description"]
    )
    # Other parameter still uses docstring
    assert (
        "Second parameter"
        in custom_tool.tool_spec["properties"]["param2"]["description"]
    )


def test_no_docstring():
    """Test handling of functions with no docstring."""

    @tool
    def minimal_tool(param: str):
        # No docstring
        return {"result": param}

    # Should not raise exceptions
    assert minimal_tool.tool_spec["name"] == "minimal_tool"
    assert "minimal_tool" in minimal_tool.tool_spec["description"]
    assert "param" in minimal_tool.tool_spec["properties"]
