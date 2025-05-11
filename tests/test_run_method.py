"""Tests for the Agent class run method."""

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


@tool
def failing_tool(param: str):
    """Sample tool that raises an exception.

    Args:
        param: Test parameter

    Returns:
        dict: Not returned because the tool fails
    """
    raise ValueError("Tool failed")


class TestAgentRunMethod:
    """Test cases for the Agent.run method."""

    @patch("minimalagent.agent.boto3")
    def test_run_simple_query(self, mock_boto3):
        """Test running a simple query without tools."""
        # Set up mock bedrock client
        mock_bedrock_client = MagicMock()
        mock_boto3.client.return_value = mock_bedrock_client

        # Mock response without tool use
        mock_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "This is a test response"}],
                }
            },
        }
        mock_bedrock_client.converse.return_value = mock_response

        # Create agent and run query
        agent = Agent(show_reasoning=False)
        response = agent.run("Hello")

        # Assert response
        assert response == "This is a test response"
        mock_bedrock_client.converse.assert_called_once()

    @patch("minimalagent.agent.boto3")
    def test_run_with_tool_use(self, mock_boto3):
        """Test running a query that uses tools."""
        # Set up mock bedrock client
        mock_bedrock_client = MagicMock()
        mock_boto3.client.return_value = mock_bedrock_client

        # Mock first response with tool use
        mock_tool_response = {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "name": "sample_tool",
                                "input": {"param": "test"},
                                "toolUseId": "12345",
                            }
                        }
                    ],
                }
            },
        }

        # Mock final response after tool use
        mock_final_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Tool returned: test"}],
                }
            },
        }

        # Configure mock to return different responses on successive calls
        mock_bedrock_client.converse.side_effect = [
            mock_tool_response, 
            mock_final_response
        ]

        # Create agent with tool and run query
        agent = Agent(tools=[sample_tool], show_reasoning=False)
        response = agent.run("Use the tool")

        # Assert response and that converse was called twice
        assert response == "Tool returned: test"
        assert mock_bedrock_client.converse.call_count == 2

    @patch("minimalagent.agent.boto3")
    def test_run_with_failing_tool(self, mock_boto3):
        """Test running a query with a tool that fails."""
        # Set up mock bedrock client
        mock_bedrock_client = MagicMock()
        mock_boto3.client.return_value = mock_bedrock_client

        # Mock first response with tool use
        mock_tool_response = {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "name": "failing_tool",
                                "input": {"param": "test"},
                                "toolUseId": "12345",
                            }
                        }
                    ],
                }
            },
        }

        # Mock final response after tool use
        mock_final_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "The tool failed"}],
                }
            },
        }

        # Configure mock to return different responses on successive calls
        mock_bedrock_client.converse.side_effect = [
            mock_tool_response, 
            mock_final_response
        ]

        # Create agent with tool and run query
        agent = Agent(tools=[failing_tool], show_reasoning=False)
        response = agent.run("Use the failing tool")

        # Assert response and that converse was called twice
        assert response == "The tool failed"
        assert mock_bedrock_client.converse.call_count == 2
    
    @patch("minimalagent.agent.boto3")
    def test_run_max_steps_reached(self, mock_boto3):
        """Test that max_steps limit is enforced."""
        # Set up mock bedrock client
        mock_bedrock_client = MagicMock()
        mock_boto3.client.return_value = mock_bedrock_client

        # Mock tool use response that will be repeated
        mock_tool_response = {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "name": "sample_tool",
                                "input": {"param": "test"},
                                "toolUseId": "12345",
                            }
                        }
                    ],
                }
            },
        }

        # Mock final response after reaching max steps
        mock_final_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Reached maximum steps"}],
                }
            },
        }

        # Configure mock to return tool responses for max_steps, then final response
        mock_bedrock_client.converse.side_effect = [mock_tool_response] * 3 + [mock_final_response]

        # Create agent with tool, max_steps=3, and run query
        agent = Agent(tools=[sample_tool], max_steps=3, show_reasoning=False)
        response = agent.run("Use the tool repeatedly")

        # Assert response and that converse was called max_steps+1 times (initial + max_steps)
        assert response == "Reached maximum steps"
        assert mock_bedrock_client.converse.call_count == 4  # Initial + 3 steps + final

    @patch("minimalagent.agent.boto3")
    def test_run_with_session_memory(self, mock_boto3):
        """Test running a query with session memory."""
        # Set up mock clients
        mock_bedrock_client = MagicMock()
        mock_ddb_client = MagicMock()
        
        # Configure boto3.client to return different clients based on service name
        def mock_client(service_name, **kwargs):
            if service_name == "bedrock-runtime":
                return mock_bedrock_client
            elif service_name == "dynamodb":
                return mock_ddb_client
            return MagicMock()
            
        mock_boto3.client.side_effect = mock_client
        
        # Mock DynamoDB query response (no previous messages)
        mock_ddb_client.query.return_value = {"Items": []}
        
        # Mock bedrock response
        mock_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "This is a session response"}],
                }
            },
        }
        mock_bedrock_client.converse.return_value = mock_response

        # Create agent with session memory and run query
        agent = Agent(use_session_memory=True, show_reasoning=False)
        response = agent.run("Hello", session_id="test_session")

        # Assert response
        assert response == "This is a session response"
        mock_ddb_client.query.assert_called_once()
        mock_ddb_client.put_item.assert_called_once()
        mock_bedrock_client.converse.assert_called_once()
    
    @patch("minimalagent.agent.boto3")
    def test_format_system_prompt(self, mock_boto3):
        """Test that system prompt is properly formatted."""
        # Set up mock bedrock client
        mock_bedrock_client = MagicMock()
        mock_boto3.client.return_value = mock_bedrock_client

        # Mock response
        mock_bedrock_client.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Response"}],
                }
            },
        }

        # Create agent with custom system prompt and run query
        agent = Agent(system_prompt="Custom instructions", show_reasoning=False)
        agent.run("Hello")

        # Get the converse call arguments
        call_args = mock_bedrock_client.converse.call_args[1]
        
        # Verify system prompt is included and properly formatted
        assert "system" in call_args
        assert isinstance(call_args["system"], list)
        assert "text" in call_args["system"][0]
        
        system_text = call_args["system"][0]["text"]
        assert "Custom instructions" in system_text
        assert "The current time and date in UTC is:" in system_text