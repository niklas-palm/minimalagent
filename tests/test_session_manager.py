"""Tests for the SessionManager class."""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import boto3
from botocore.exceptions import ClientError

from minimalagent.models import Reasoning, ReasoningStep, ToolData
from minimalagent.session import SessionManager


class TestSessionManager(unittest.TestCase):
    """Test cases for the SessionManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a mock logger
        self.mock_logger = MagicMock()
        self.mock_logger.debug = MagicMock()
        self.mock_logger.info = MagicMock()
        self.mock_logger.warning = MagicMock()
        self.mock_logger.error = MagicMock()

        # Mock boto3 to return our mock clients
        self.session_id = f"test-session-{int(time.time())}"

        # Create patcher for boto3 client
        self.boto3_patch = patch("boto3.client")
        self.mock_boto3_client = self.boto3_patch.start()

        # Create a mock DynamoDB client for tests that use self.session_manager directly
        self.mock_ddb = MagicMock()
        self.mock_boto3_client.return_value = self.mock_ddb

        # Create a session manager for tests that need one
        self.session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

    def tearDown(self):
        """Clean up after tests."""
        self.boto3_patch.stop()

    def test_initialization(self):
        """Test initialization of SessionManager."""
        # Create mock for DynamoDB
        mock_ddb = MagicMock()
        self.mock_boto3_client.return_value = mock_ddb

        # Create SessionManager
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

        # Verify that DynamoDB client was initialized with correct parameters
        self.mock_boto3_client.assert_any_call("dynamodb", region_name="us-west-2")
        self.assertEqual(session_manager.session_table_name, "test-table")
        self.assertEqual(session_manager.session_ttl, 3600)
        self.assertEqual(session_manager.use_session_memory, True)
        self.assertEqual(session_manager.ddb_client, mock_ddb)

    def test_initialization_with_error(self):
        """Test initialization with DynamoDB client error."""
        # Mock boto3 to raise an exception
        self.mock_boto3_client.side_effect = ClientError(
            {
                "Error": {
                    "Code": "UnrecognizedClientException",
                    "Message": "Invalid credentials",
                }
            },
            "CreateTable",
        )

        # Create SessionManager with error
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

        # Verify that session memory was disabled
        self.assertEqual(session_manager.use_session_memory, False)
        self.assertEqual(session_manager.session_table_name, None)
        self.assertEqual(session_manager.ddb_client, None)

    def test_is_valid_session_id(self):
        """Test session_id validation."""
        # Test valid session IDs
        self.assertTrue(self.session_manager.is_valid_session_id("valid-id"))
        self.assertTrue(self.session_manager.is_valid_session_id("valid_id_123"))
        self.assertTrue(self.session_manager.is_valid_session_id("123"))
        self.assertTrue(self.session_manager.is_valid_session_id("a" * 128))

        # Test invalid session IDs
        self.assertFalse(self.session_manager.is_valid_session_id(""))
        self.assertFalse(
            self.session_manager.is_valid_session_id("a" * 129)
        )  # Too long
        self.assertFalse(
            self.session_manager.is_valid_session_id("invalid/id")
        )  # Invalid char
        self.assertFalse(
            self.session_manager.is_valid_session_id("invalid id")
        )  # Space
        self.assertFalse(
            self.session_manager.is_valid_session_id("invalid!id")
        )  # Invalid char

    def test_is_valid_table_name(self):
        """Test table_name validation."""
        # Test valid table names
        self.assertTrue(self.session_manager.is_valid_table_name("valid-table"))
        self.assertTrue(self.session_manager.is_valid_table_name("valid_table_123"))
        self.assertTrue(self.session_manager.is_valid_table_name("table.with.dots"))
        self.assertTrue(self.session_manager.is_valid_table_name("a" * 255))

        # Test invalid table names
        self.assertFalse(self.session_manager.is_valid_table_name(""))
        self.assertFalse(self.session_manager.is_valid_table_name("ab"))  # Too short
        self.assertFalse(
            self.session_manager.is_valid_table_name("a" * 256)
        )  # Too long
        self.assertFalse(
            self.session_manager.is_valid_table_name("invalid table")
        )  # Space
        self.assertFalse(
            self.session_manager.is_valid_table_name("invalid!table")
        )  # Invalid char

    def test_ensure_session_table_existing(self):
        """Test ensuring session table exists when it already exists."""
        # Create mock for DynamoDB
        mock_ddb = MagicMock()
        mock_ddb.describe_table.return_value = {"Table": {"TableName": "test-table"}}
        self.mock_boto3_client.return_value = mock_ddb

        # Create session manager
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

        # Reset mock to clear initialization calls
        mock_ddb.reset_mock()

        # Call ensure_session_table
        result = session_manager.ensure_session_table()

        # Verify that describe_table was called but not create_table
        mock_ddb.describe_table.assert_called_once_with(TableName="test-table")
        mock_ddb.create_table.assert_not_called()
        self.assertTrue(result)

    def test_ensure_session_table_creation(self):
        """Test ensuring session table exists when it needs to be created."""
        # Create mock for DynamoDB
        mock_ddb = MagicMock()
        mock_ddb.describe_table.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Table not found",
                }
            },
            "DescribeTable",
        )
        # Create waiter mock
        mock_waiter = MagicMock()
        mock_ddb.get_waiter.return_value = mock_waiter

        self.mock_boto3_client.return_value = mock_ddb

        # Create session manager
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

        # Reset mock to clear initialization calls
        mock_ddb.reset_mock()

        # Set up describe table again for subsequent test
        mock_ddb.describe_table.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "Table not found",
                }
            },
            "DescribeTable",
        )

        # Call ensure_session_table
        result = session_manager.ensure_session_table()

        # Verify that create_table was called
        mock_ddb.describe_table.assert_called_once_with(TableName="test-table")
        mock_ddb.create_table.assert_called_once()
        mock_ddb.update_time_to_live.assert_called_once()
        self.assertTrue(result)

    def test_ensure_session_table_error(self):
        """Test ensuring session table with unexpected error."""
        # Create mock for DynamoDB
        mock_ddb = MagicMock()
        mock_ddb.describe_table.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeTable",
        )
        self.mock_boto3_client.return_value = mock_ddb

        # Create session manager
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

        # Reset mock and set side effect again
        mock_ddb.reset_mock()
        mock_ddb.describe_table.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DescribeTable",
        )

        # Call ensure_session_table
        result = session_manager.ensure_session_table()

        # Verify error was handled and use_session_memory was disabled
        self.assertFalse(result)
        self.assertEqual(session_manager.use_session_memory, False)
        self.assertEqual(session_manager.session_table_name, None)

    def test_get_session_messages(self):
        """Test get_session_messages method."""
        # Create mock for DynamoDB
        mock_ddb = MagicMock()
        mock_messages = [{"role": "user", "content": [{"text": "Hello"}]}]
        mock_ddb.query.return_value = {
            "Items": [
                {
                    "pk": {"S": f"messages#{self.session_id}"},
                    "sk": {"N": "1234567890"},
                    "messages": {"S": json.dumps(mock_messages)},
                }
            ]
        }
        self.mock_boto3_client.return_value = mock_ddb

        # Create session manager
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            session_table_name="test-table",
            memory_region="us-west-2",
            session_ttl=3600,
            show_reasoning=True,
        )

        # Reset mock to clear initialization calls
        mock_ddb.reset_mock()

        # Call get_session_messages
        result = session_manager.get_session_messages(self.session_id)

        # Verify the result
        self.assertEqual(result, mock_messages)
        mock_ddb.query.assert_called_once()

        # Verify the query parameters - checking for ScanIndexForward=False and Limit=1
        args, kwargs = mock_ddb.query.call_args
        self.assertEqual(kwargs["TableName"], "test-table")
        self.assertEqual(kwargs["ScanIndexForward"], False)
        self.assertEqual(kwargs["Limit"], 1)

        # Test with invalid session ID
        result = self.session_manager.get_session_messages("invalid/id")
        self.assertEqual(result, [])

    def test_save_session_messages(self):
        """Test save_session_messages method."""
        # Create test messages
        messages = [
            {"role": "user", "content": [{"text": "Hello"}]},
            {"role": "assistant", "content": [{"text": "Hi there!"}]},
        ]

        # Call save_session_messages
        result = self.session_manager.save_session_messages(self.session_id, messages)

        # Verify the result
        self.assertTrue(result)
        self.mock_ddb.put_item.assert_called_once()
        args, kwargs = self.mock_ddb.put_item.call_args
        self.assertEqual(kwargs["TableName"], "test-table")
        self.assertEqual(kwargs["Item"]["pk"]["S"], f"messages#{self.session_id}")

        # Test with invalid session ID
        result = self.session_manager.save_session_messages("invalid/id", messages)
        self.assertFalse(result)

    def test_get_reasoning(self):
        """Test get_reasoning method."""
        # Mock DynamoDB query response
        mock_reasoning_dict = {
            "query": "Test query",
            "steps": [{"step_number": 1, "thinking": "Test thinking"}],
            "total_steps": 1,
            "truncated": False,
            "exceeded_size_limit": False,
        }
        self.mock_ddb.query.return_value = {
            "Items": [{"reasoning": {"S": json.dumps(mock_reasoning_dict)}}]
        }

        # Create expected Reasoning object
        expected_reasoning = Reasoning.from_dict(mock_reasoning_dict)

        # Call get_reasoning
        result = self.session_manager.get_reasoning(self.session_id)

        # Verify the result
        self.assertEqual(result.query, expected_reasoning.query)
        self.assertEqual(result.total_steps, expected_reasoning.total_steps)
        self.assertEqual(result.steps[0].thinking, expected_reasoning.steps[0].thinking)
        self.assertEqual(
            result.steps[0].step_number, expected_reasoning.steps[0].step_number
        )
        self.mock_ddb.query.assert_called_once()

        # Test with invalid session ID
        result = self.session_manager.get_reasoning("invalid/id")
        self.assertIsInstance(result, Reasoning)
        self.assertEqual(result.query, None)

    def test_get_reasoning_history(self):
        """Test get_reasoning_history method."""
        # Mock DynamoDB query response
        mock_reasoning1_dict = {
            "query": "First query",
            "steps": [{"step_number": 1, "thinking": "First thinking"}],
            "total_steps": 1,
            "truncated": False,
            "exceeded_size_limit": False,
        }
        mock_reasoning2_dict = {
            "query": "Second query",
            "steps": [{"step_number": 1, "thinking": "Second thinking"}],
            "total_steps": 1,
            "truncated": False,
            "exceeded_size_limit": False,
        }
        self.mock_ddb.query.return_value = {
            "Items": [
                {"reasoning": {"S": json.dumps(mock_reasoning1_dict)}},
                {"reasoning": {"S": json.dumps(mock_reasoning2_dict)}},
            ]
        }

        # Create expected Reasoning objects
        expected_reasoning1 = Reasoning.from_dict(mock_reasoning1_dict)
        expected_reasoning2 = Reasoning.from_dict(mock_reasoning2_dict)

        # Call get_reasoning_history
        result = self.session_manager.get_reasoning_history(self.session_id)

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].query, expected_reasoning1.query)
        self.assertEqual(
            result[0].steps[0].thinking, expected_reasoning1.steps[0].thinking
        )
        self.assertEqual(result[1].query, expected_reasoning2.query)
        self.assertEqual(
            result[1].steps[0].thinking, expected_reasoning2.steps[0].thinking
        )
        self.mock_ddb.query.assert_called_once()

        # Test with invalid session ID
        result = self.session_manager.get_reasoning_history("invalid/id")
        self.assertEqual(result, [])

    def test_update_reasoning(self):
        """Test update_reasoning method."""
        # Call update_reasoning with no existing reasoning
        result = self.session_manager.update_reasoning(
            reasoning=None, thinking="Test thinking", step_number=1
        )

        # Verify the result
        self.assertIsInstance(result, Reasoning)
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.steps[0].thinking, "Test thinking")
        self.assertEqual(result.steps[0].step_number, 1)

        # Call update_reasoning with existing reasoning
        result = self.session_manager.update_reasoning(
            reasoning=result,
            thinking="More thinking",
            tool_data=[{"name": "test_tool", "inputs": {"a": 1}}],
            step_number=2,
        )

        # Verify the result
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(len(result.steps), 2)
        self.assertEqual(result.steps[1].thinking, "More thinking")
        self.assertEqual(len(result.steps[1].tools), 1)
        self.assertEqual(result.steps[1].tools[0].name, "test_tool")

    def test_save_reasoning_data(self):
        """Test save_reasoning_data method."""
        # Create test reasoning data
        timestamp = int(time.time())
        step = ReasoningStep(
            step_number=1, thinking="Test thinking", timestamp=timestamp
        )
        reasoning = Reasoning(
            session_id=self.session_id, query="Test query", steps=[step], total_steps=1
        )

        # Call save_reasoning_data
        result = self.session_manager.save_reasoning_data(self.session_id, reasoning)

        # Verify the result
        self.assertTrue(result)
        self.mock_ddb.put_item.assert_called_once()
        args, kwargs = self.mock_ddb.put_item.call_args
        self.assertEqual(kwargs["TableName"], "test-table")
        self.assertEqual(kwargs["Item"]["pk"]["S"], f"reasoning#{self.session_id}")

        # Test with invalid session ID
        result = self.session_manager.save_reasoning_data("invalid/id", reasoning)
        self.assertFalse(result)

    def test_update_reasoning_if_needed(self):
        """Test update_reasoning_if_needed method."""
        # Create a session manager with real_time_reasoning enabled
        session_manager = SessionManager(
            logger=self.mock_logger,
            use_session_memory=True,
            real_time_reasoning=True,
            session_table_name="test-table",
        )

        # Add a save_reasoning_data mock
        session_manager.save_reasoning_data = MagicMock(return_value=True)

        # Call update_reasoning_if_needed with a Reasoning object
        reasoning = Reasoning(session_id=self.session_id, query="Test")
        result = session_manager.update_reasoning_if_needed(reasoning, self.session_id)

        # Verify the result
        self.assertTrue(result)
        session_manager.save_reasoning_data.assert_called_once_with(
            self.session_id, reasoning
        )

        # Test with real_time_reasoning disabled
        session_manager.real_time_reasoning = False
        result = session_manager.update_reasoning_if_needed(reasoning, self.session_id)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
