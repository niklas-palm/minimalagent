"""Tests for the Agent class."""

# Standard library imports
from unittest.mock import MagicMock, patch

import pytest

# Project imports
from minimalagent import Agent, tool


@tool
def sample_tool(param: str):
    """Sample tool for testing.

    Args:
        param: Test parameter

    Returns:
        dict: Response containing the parameter
    """
    return {"param": param}


class TestAgent:
    """Test cases for the Agent class."""

    def test_initialization(self):
        """Test that the agent initializes correctly with default values."""
        agent = Agent(tools=[sample_tool])

        # Verify model configuration
        assert (
            agent.model_id == "us.amazon.nova-pro-v1:0"
        ), "Default model ID should be nova-pro"
        assert (
            agent.bedrock_region == "us-west-2"
        ), "Default bedrock_region should be us-west-2"
        assert (
            agent.memory_region == "us-west-2"
        ), "Default memory_region should be same as bedrock_region"

        # Verify behavior configuration
        assert agent.max_steps == 5, "Default max_steps should be 5"
        assert agent.show_reasoning is True, "Default show_reasoning should be True"

        # Verify session configuration
        assert (
            agent.use_session_memory is False
        ), "Default session memory should be disabled"
        assert (
            agent.session_table_name is None
        ), "Default session table name should be None"

    def test_add_tools(self):
        """Test adding tools to the agent."""
        # Create agent with no tools
        agent = Agent()
        assert len(agent.tool_config["tools"]) == 0

        # Add the sample tool
        agent.add_tools([sample_tool])
        assert len(agent.tool_config["tools"]) == 1
        assert agent.tool_functions.get("sample_tool") is not None

    def test_clear_tools(self):
        """Test clearing tools from the agent."""
        # Create agent with a tool
        agent = Agent(tools=[sample_tool])
        assert len(agent.tool_config["tools"]) == 1

        # Clear the tools
        agent.clear_tools()
        assert len(agent.tool_config["tools"]) == 0
        assert len(agent.tool_functions) == 0

    @patch("minimalagent.agent.boto3")
    def test_session_initialization(self, mock_boto3):
        """Test session initialization logic."""
        # Set up mocks
        mock_ddb_client = MagicMock()
        mock_boto3.client.return_value = mock_ddb_client

        # Test explicit opt-in
        agent = Agent(use_session_memory=True)
        assert agent.use_session_memory is True
        assert agent.session_table_name == "minimalagent-session-table"
        mock_boto3.client.assert_any_call("dynamodb", region_name="us-west-2")
        assert mock_ddb_client.describe_table.called

        # Test implied opt-in with custom table name
        mock_boto3.reset_mock()
        mock_ddb_client.reset_mock()
        agent = Agent(session_table_name="custom-table")
        assert agent.use_session_memory is True
        assert agent.session_table_name == "custom-table"
        mock_boto3.client.assert_any_call("dynamodb", region_name="us-west-2")
        assert mock_ddb_client.describe_table.called

        # Test with custom memory region
        mock_boto3.reset_mock()
        mock_ddb_client.reset_mock()
        agent = Agent(use_session_memory=True, memory_region="us-east-1")
        assert agent.use_session_memory is True
        assert agent.memory_region == "us-east-1"
        assert agent.bedrock_region == "us-west-2"  # Should still use default
        mock_boto3.client.assert_any_call("dynamodb", region_name="us-east-1")
        assert mock_ddb_client.describe_table.called

    @patch("minimalagent.agent.boto3")
    def test_run_with_error_handling(self, mock_boto3):
        """Test run method with error handling for AWS credentials."""
        # Set up mock to raise exception
        mock_boto3.client.side_effect = Exception(
            "Could not connect to the endpoint URL"
        )

        # Should catch the exception and provide a helpful error message
        with pytest.raises(RuntimeError) as excinfo:
            agent = Agent()

        assert "AWS credentials not found or invalid" in str(excinfo.value)
