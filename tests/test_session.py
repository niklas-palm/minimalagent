"""Tests for the session persistence functionality."""

# Standard library imports
import json
from unittest.mock import MagicMock, patch

# Third-party imports
import pytest
from botocore.exceptions import ClientError

# Project imports
from minimalagent import Agent, tool


@tool
def echo(text: str):
    """Echo the input text.

    Args:
        text: Text to echo

    Returns:
        dict: Echoed text
    """
    return {"text": text}


class TestSessionPersistence:
    """Test cases for session persistence functionality."""

    @patch("minimalagent.agent.boto3")
    def test_get_session_messages(self, mock_boto3):
        """Test retrieving session messages from DynamoDB."""
        # Set up mocks
        mock_ddb_client = MagicMock()
        mock_boto3.client.return_value = mock_ddb_client

        # Mock DynamoDB response
        mock_messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ]
        mock_ddb_client.query.return_value = {
            "Items": [
                {
                    "session_id": {"S": "test_session"},
                    "timestamp": {"N": "1234567890"},
                    "messages": {"S": json.dumps(mock_messages)},
                    "expiration_time": {"N": "1234657890"},
                }
            ]
        }

        # Create agent with session support
        agent = Agent(use_session_memory=True)

        # Call the method directly for testing
        result = agent._get_session_messages("test_session")

        # Check the result
        assert result == mock_messages
        mock_ddb_client.query.assert_called_once()

    @patch("minimalagent.agent.boto3")
    def test_save_session_messages(self, mock_boto3):
        """Test saving session messages to DynamoDB."""
        # Set up mocks
        mock_ddb_client = MagicMock()
        mock_boto3.client.return_value = mock_ddb_client

        # Create agent with session support
        agent = Agent(use_session_memory=True)

        # Test messages
        mock_messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ]

        # Call the method directly for testing
        result = agent._save_session_messages("test_session", mock_messages)

        # Check the result
        assert result is True
        mock_ddb_client.put_item.assert_called_once()

    @patch("minimalagent.agent.boto3")
    def test_session_table_creation(self, mock_boto3):
        """Test creation of DynamoDB table for sessions."""
        # Set up mocks
        mock_ddb_client = MagicMock()
        mock_boto3.client.return_value = mock_ddb_client

        # Make describe_table raise ClientError to trigger table creation
        mock_error_response = {
            "Error": {"Code": "ResourceNotFoundException", "Message": "Table not found"}
        }
        mock_ddb_client.describe_table.side_effect = ClientError(
            mock_error_response, "DescribeTable"
        )

        # Create a waiter mock
        mock_waiter = MagicMock()
        mock_ddb_client.get_waiter.return_value = mock_waiter

        # Create agent with session support
        agent = Agent(use_session_memory=True)

        # Check that table creation was attempted
        mock_ddb_client.create_table.assert_called_once()
        mock_ddb_client.get_waiter.assert_called_once_with("table_exists")
        mock_waiter.wait.assert_called_once()
        mock_ddb_client.update_time_to_live.assert_called_once()
