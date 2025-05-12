"""Tests for parameter validation in MinimalAgent."""

from unittest.mock import MagicMock, patch

import pytest

from minimalagent import Agent, tool


# Sample tools for testing
@tool
def sample_tool_1(param_str: str):
    """Test tool 1.

    Args:
        param_str: Test parameter

    Returns:
        dict: Test result
    """
    return {"result": param_str}


@tool
def sample_tool_2(param_str: str):
    """Test tool 2.

    Args:
        param_str: Test parameter

    Returns:
        dict: Test result
    """
    return {"result": param_str}


# Helper regular function (not a tool)
def not_a_tool(param):
    return param


class TestParameterValidation:
    """Test cases for parameter validation."""

    @patch("minimalagent.agent.boto3")
    def test_max_steps_validation(self, mock_boto3):
        """Test validation of max_steps parameter."""
        # Mock clients
        mock_boto3.client.return_value = MagicMock()

        # Test valid max_steps
        agent = Agent(max_steps=1)  # Min value
        agent = Agent(max_steps=100)  # Larger value

        # Test invalid max_steps
        with pytest.raises(ValueError, match="max_steps must be greater than 0"):
            Agent(max_steps=0)

        with pytest.raises(ValueError, match="max_steps must be greater than 0"):
            Agent(max_steps=-5)

    @patch("minimalagent.agent.boto3")
    def test_session_ttl_validation(self, mock_boto3):
        """Test validation of session_ttl parameter."""
        # Mock clients
        mock_boto3.client.return_value = MagicMock()

        # Test valid session_ttl
        agent = Agent(session_ttl=1)  # Min value
        agent = Agent(session_ttl=86400)  # 1 day

        # Test invalid session_ttl
        with pytest.raises(ValueError, match="session_ttl must be greater than 0"):
            Agent(session_ttl=0)

        with pytest.raises(ValueError, match="session_ttl must be greater than 0"):
            Agent(session_ttl=-60)

    @patch("minimalagent.agent.boto3")
    def test_table_name_validation(self, mock_boto3):
        """Test validation of session_table_name parameter."""
        # Mock clients
        mock_boto3.client.return_value = MagicMock()

        # Create agent for validation tests
        agent = Agent()

        # Test valid table names
        assert agent.session_manager.is_valid_table_name("my-table") is True
        assert agent.session_manager.is_valid_table_name("my_table_123") is True
        assert agent.session_manager.is_valid_table_name("table.with.dots") is True

        # Test invalid table names
        assert agent.session_manager.is_valid_table_name("") is False
        assert (
            agent.session_manager.is_valid_table_name("ab") is False
        )  # Too short (< 3 chars)
        assert (
            agent.session_manager.is_valid_table_name("table with spaces") is False
        )  # Contains spaces
        assert (
            agent.session_manager.is_valid_table_name("table!@#$") is False
        )  # Invalid characters

    @patch("minimalagent.agent.boto3")
    def test_session_id_validation(self, mock_boto3):
        """Test validation of session_id parameter."""
        # Mock clients
        mock_boto3.client.return_value = MagicMock()

        # Create agent with session memory
        agent = Agent(use_session_memory=True)

        # Test valid session ID
        assert agent.session_manager.is_valid_session_id("valid-session-id-123") is True
        assert agent.session_manager.is_valid_session_id("validID") is True

        # Test invalid session IDs
        assert agent.session_manager.is_valid_session_id("") is False
        assert (
            agent.session_manager.is_valid_session_id("session/with/slashes") is False
        )
        assert agent.session_manager.is_valid_session_id("session with spaces") is False

        # Very long session ID (> 128 chars)
        long_id = "a" * 129
        assert agent.session_manager.is_valid_session_id(long_id) is False

    @patch("minimalagent.agent.boto3")
    def test_tools_validation(self, mock_boto3):
        """Test validation of tools parameter."""
        # Mock clients
        mock_boto3.client.return_value = MagicMock()

        # Test valid tools
        agent = Agent(tools=[sample_tool_1])
        agent = Agent(tools=[sample_tool_1, sample_tool_2])

        # Test with non-list
        with pytest.raises(ValueError, match="Invalid tools parameter"):
            Agent(tools=sample_tool_1)  # Not a list

        # Test with non-callable
        with pytest.raises(ValueError, match="Invalid tools parameter"):
            Agent(tools=[sample_tool_1, "not_a_tool"])

        # Test with function not decorated with @tool
        with pytest.raises(ValueError, match="Invalid tools parameter"):
            Agent(tools=[sample_tool_1, not_a_tool])

    @patch("minimalagent.agent.boto3")
    def test_add_tools_validation(self, mock_boto3):
        """Test validation in add_tools method."""
        # Mock clients
        mock_boto3.client.return_value = MagicMock()

        # Create agent
        agent = Agent()

        # Test adding valid tools (first one should succeed)
        agent.add_tools([sample_tool_1])

        # Test adding empty list (should work)
        agent.add_tools([])

        # Create a new agent for these tests to avoid the duplicate tool issue
        agent2 = Agent()

        # Test with non-list
        with pytest.raises(TypeError, match="tools must be a list"):
            agent2.add_tools(sample_tool_1)

        # Test with non-callable
        with pytest.raises(TypeError, match="not callable"):
            agent2.add_tools([sample_tool_1, "not_a_tool"])

        # Test with function not decorated with @tool
        with pytest.raises(ValueError, match="must be decorated with @tool"):
            agent2.add_tools([not_a_tool])

        # Test adding duplicate tool (using original agent that already has sample_tool_1)
        with pytest.raises(ValueError, match="tool with name .* already exists"):
            agent.add_tools([sample_tool_1])  # Already added above
