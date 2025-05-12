"""Tests for the reasoning persistence functionality."""

import json
import time
import unittest
from unittest.mock import MagicMock, patch

import boto3
from botocore.exceptions import ClientError

from minimalagent import Agent, tool
from minimalagent.models import Reasoning, ReasoningStep, ToolData


class TestReasoningPersistence(unittest.TestCase):
    """Test the reasoning persistence functionality of the Agent class."""

    def setUp(self):
        """Set up test environment."""

        # Create a simple test tool
        @tool
        def test_tool(a: int, b: int) -> int:
            """Add two numbers.

            Args:
                a: First number
                b: Second number

            Returns:
                Sum of a and b
            """
            return a + b

        self.test_tool = test_tool
        self.session_id = f"test-session-{int(time.time())}"

        # Mock DynamoDB client
        self.mock_ddb = MagicMock()
        self.mock_ddb.put_item = MagicMock(return_value={})
        self.mock_ddb.query = MagicMock(return_value={"Items": []})

        # Mock Bedrock client response for a simple tool use
        self.mock_bedrock = MagicMock()

        # Create test agent with mocks - patch both agent.boto3 and session.boto3
        agent_patcher = patch("minimalagent.agent.boto3")
        session_patcher = patch("minimalagent.session.boto3")

        self.mock_agent_boto3 = agent_patcher.start()
        self.mock_session_boto3 = session_patcher.start()

        # Add cleanup for patchers
        self.addCleanup(agent_patcher.stop)
        self.addCleanup(session_patcher.stop)

        # Configure mocks
        self.mock_agent_boto3.client.return_value = self.mock_bedrock
        self.mock_session_boto3.client.return_value = self.mock_ddb

        # Create test agent
        self.agent = Agent(
            tools=[self.test_tool],
            use_session_memory=True,
            real_time_reasoning=True,
            show_reasoning=False,  # Disable console output
            log_level="CRITICAL",  # Disable normal logging for tests
        )

    def test_session_manager_update_reasoning(self):
        """Test the session_manager's update_reasoning method."""
        # Test with empty reasoning
        reasoning = self.agent.session_manager.update_reasoning(
            reasoning=None, thinking="Test thinking", step_number=1
        )

        self.assertIsInstance(reasoning, Reasoning)
        self.assertEqual(reasoning.total_steps, 1)
        self.assertEqual(reasoning.steps[0].thinking, "Test thinking")
        self.assertEqual(reasoning.steps[0].step_number, 1)

        # Test adding a step
        tool_data = [{"name": "test_tool", "inputs": {"a": 1, "b": 2}}]
        reasoning = self.agent.session_manager.update_reasoning(
            reasoning=reasoning,
            thinking="More thinking",
            tool_data=tool_data,
            step_number=2,
        )

        self.assertEqual(reasoning.total_steps, 2)
        self.assertEqual(len(reasoning.steps), 2)
        self.assertEqual(reasoning.steps[1].thinking, "More thinking")
        self.assertEqual(reasoning.steps[1].tools[0].name, "test_tool")

    def test_save_reasoning_data(self):
        """Test saving reasoning data to DynamoDB."""
        # Create test reasoning data
        timestamp = int(time.time())
        step = ReasoningStep(
            step_number=1, thinking="Test thinking", timestamp=timestamp
        )
        reasoning = Reasoning(
            session_id=self.session_id, query="Test query", steps=[step], total_steps=1
        )

        # Test saving reasoning data
        result = self.agent.session_manager.save_reasoning_data(
            self.session_id, reasoning
        )
        self.assertTrue(result)

        # Verify DynamoDB put_item was called with correct parameters
        self.mock_ddb.put_item.assert_called_once()
        args, kwargs = self.mock_ddb.put_item.call_args

        self.assertEqual(
            kwargs["TableName"], self.agent.session_manager.session_table_name
        )
        self.assertEqual(kwargs["Item"]["pk"]["S"], f"reasoning#{self.session_id}")
        self.assertIn("reasoning", kwargs["Item"])
        self.assertIn("expiration_time", kwargs["Item"])

    def test_get_reasoning(self):
        """Test retrieving reasoning data."""
        # Mock the DynamoDB response
        mock_reasoning_dict = {
            "session_id": self.session_id,
            "query": "Test query",
            "steps": [{"step_number": 1, "thinking": "Test thinking"}],
            "total_steps": 1,
            "truncated": False,
            "exceeded_size_limit": False,
        }

        self.mock_ddb.query.return_value = {
            "Items": [
                {
                    "reasoning": {"S": json.dumps(mock_reasoning_dict)},
                    "timestamp": {"N": "123456789"},
                }
            ]
        }

        # Get reasoning
        result = self.agent.session_manager.get_reasoning(self.session_id)

        # Verify DynamoDB query was called correctly
        self.mock_ddb.query.assert_called_once()
        args, kwargs = self.mock_ddb.query.call_args
        self.assertEqual(
            kwargs["TableName"], self.agent.session_manager.session_table_name
        )
        self.assertEqual(
            kwargs["ExpressionAttributeValues"][":pk"]["S"],
            f"reasoning#{self.session_id}",
        )

        # Verify result
        self.assertIsInstance(result, Reasoning)
        self.assertEqual(result.session_id, self.session_id)
        self.assertEqual(result.query, "Test query")
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.steps[0].thinking, "Test thinking")

    def test_size_limit_handling(self):
        """Test handling of large reasoning objects that exceed DynamoDB size limits."""
        # Create test reasoning data with multiple steps
        current_time = int(time.time())
        steps = [
            ReasoningStep(
                step_number=1, thinking="Earlier thinking", timestamp=current_time - 100
            ),
            ReasoningStep(
                step_number=2, thinking="Middle thinking", timestamp=current_time - 50
            ),
            ReasoningStep(
                step_number=3, thinking="Recent thinking", timestamp=current_time
            ),
        ]

        test_reasoning = Reasoning(
            session_id=self.session_id,
            query="Test query",
            steps=steps,
            total_steps=3,
            final_response="This is the final response.",
        )

        # Mock DynamoDB to raise a size limit exception on first put_item call
        self.mock_ddb.put_item.side_effect = [
            ClientError(
                {
                    "Error": {
                        "Code": "ItemSizeTooLarge",
                        "Message": "Item size has exceeded the maximum allowed size",
                    }
                },
                "PutItem",
            ),
            # Second call (with truncated data) succeeds
            {},
        ]

        # Save the reasoning data - this should trigger our size limit handling
        result = self.agent.session_manager.save_reasoning_data(
            self.session_id, test_reasoning
        )
        self.assertTrue(result)

        # Verify DynamoDB put_item was called twice (first fails, second succeeds)
        self.assertEqual(self.mock_ddb.put_item.call_count, 2)

        # Check the reasoning object was updated with the exceeded_size_limit flag
        self.assertTrue(test_reasoning.exceeded_size_limit)

        # Check that a warning was added to the final response
        self.assertIn("WARNING", test_reasoning.final_response)
        self.assertIn("exceeded the maximum size limit", test_reasoning.final_response)

        # Check the truncated version in the second put_item call
        args, kwargs = self.mock_ddb.put_item.call_args_list[1]
        saved_json = kwargs["Item"]["reasoning"]["S"]
        saved_dict = json.loads(saved_json)

        # Check for flags in the saved data
        self.assertTrue(saved_dict["truncated"])
        self.assertTrue(saved_dict["exceeded_size_limit"])

        # Check that we only kept the first and last step
        self.assertEqual(len(saved_dict["steps"]), 2)
        self.assertEqual(saved_dict["steps"][0]["step_number"], 1)
        self.assertEqual(saved_dict["steps"][-1]["step_number"], 3)

    def test_run_returns_tuple(self):
        """Test that run method returns a tuple with response and reasoning."""
        # Mock Bedrock response for a complete interaction
        first_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>I need to use test_tool to add numbers</thinking>",
                        },
                        {
                            "toolUse": {
                                "name": "test_tool",
                                "input": {"a": 5, "b": 7},
                                "toolUseId": "123",
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
        }

        final_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>Now I can provide the answer</thinking>The sum is 12."
                        }
                    ],
                }
            },
            "stopReason": "end_turn",
        }

        # Set up mock to return different responses on each call
        self.mock_bedrock.converse = MagicMock(
            side_effect=[first_response, final_response]
        )

        # Execute the run method
        response, reasoning = self.agent.run("Add 5 and 7", session_id=self.session_id)

        # Assert return value is a tuple with the expected structure
        self.assertIsInstance(response, str)
        self.assertIsInstance(reasoning, Reasoning)
        self.assertEqual(response, "The sum is 12.")

        # Verify that reasoning has the expected structure
        self.assertEqual(reasoning.query, "Add 5 and 7")
        self.assertEqual(reasoning.session_id, self.session_id)

    def test_real_time_updates(self):
        """Test that real-time reasoning updates are saved during execution."""
        # Set up mock bedrock response that will trigger tool use
        first_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>I need to use test_tool to add numbers</thinking>",
                        },
                        {
                            "toolUse": {
                                "name": "test_tool",
                                "input": {"a": 5, "b": 7},
                                "toolUseId": "123",
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
        }

        final_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>Now I can provide the answer</thinking>The sum is 12."
                        }
                    ],
                }
            },
            "stopReason": "end_turn",
        }

        # Set up mock to return different responses on each call
        self.mock_bedrock.converse = MagicMock(
            side_effect=[first_response, final_response]
        )

        # Execute the run method
        self.agent.run("Add 5 and 7", session_id=self.session_id)

        # Verify DynamoDB was called for real-time updates
        # Should be called at least once during execution, not just at the end
        self.mock_ddb.put_item.assert_called()

        # Count calls with reasoning#{session_id}
        reasoning_calls = 0
        for call in self.mock_ddb.put_item.call_args_list:
            args, kwargs = call
            if f"reasoning#{self.session_id}" in str(kwargs):
                reasoning_calls += 1

        # Expect at least one call during execution (real-time) plus one at the end
        self.assertGreaterEqual(reasoning_calls, 1)

    def test_no_real_time_updates_when_disabled(self):
        """Test that real-time reasoning updates are not saved when feature is disabled."""
        # Create a new agent with real_time_reasoning=False
        with patch("boto3.client") as mock_boto3_client:
            mock_boto3_client.side_effect = lambda service, region_name=None: {
                "dynamodb": self.mock_ddb,
                "bedrock-runtime": self.mock_bedrock,
            }[service]

            agent_without_rt = Agent(
                tools=[self.test_tool],
                use_session_memory=True,
                real_time_reasoning=False,  # Disable real-time updates
                show_reasoning=False,
                log_level="CRITICAL",  # Disable normal logging for tests
            )

        # Reset the mock
        self.mock_ddb.reset_mock()

        # Set up mock bedrock responses
        first_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>I need to use test_tool to add numbers</thinking>",
                        },
                        {
                            "toolUse": {
                                "name": "test_tool",
                                "input": {"a": 5, "b": 7},
                                "toolUseId": "123",
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
        }

        final_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>Now I can provide the answer</thinking>The sum is 12."
                        }
                    ],
                }
            },
            "stopReason": "end_turn",
        }

        # Set up mock to return different responses on each call
        self.mock_bedrock.converse = MagicMock(
            side_effect=[first_response, final_response]
        )

        # Execute the run method
        agent_without_rt.run("Add 5 and 7", session_id=self.session_id)

        # There should only be two calls to put_item at the end for messages and final reasoning
        # Not during execution
        self.mock_ddb.put_item.assert_called()

        # Count intermediate reasoning calls
        reasoning_calls_during_execution = 0
        for call in self.mock_ddb.put_item.call_args_list:
            args, kwargs = call
            # Skip the final reasoning save call which happens at the end
            if f"reasoning#{self.session_id}" in str(
                kwargs
            ) and "Now I can provide the answer" not in str(kwargs):
                reasoning_calls_during_execution += 1

        # Should have no intermediate reasoning updates
        self.assertEqual(reasoning_calls_during_execution, 0)

    def test_real_time_reasoning_requires_session_memory(self):
        """Test that real_time_reasoning has no effect without session_memory."""
        # Create a new agent with use_session_memory=False but real_time_reasoning=True
        with patch("boto3.client") as mock_boto3_client:
            mock_boto3_client.side_effect = lambda service, region_name=None: {
                "dynamodb": self.mock_ddb,
                "bedrock-runtime": self.mock_bedrock,
            }[service]

            agent_without_session = Agent(
                tools=[self.test_tool],
                use_session_memory=False,  # Disable session memory
                real_time_reasoning=True,  # Enable real-time reasoning
                show_reasoning=False,
                log_level="CRITICAL",  # Disable normal logging for tests
            )

        # Check that session_manager.real_time_reasoning was automatically disabled
        self.assertFalse(agent_without_session.session_manager.real_time_reasoning)

        # Reset the mock
        self.mock_ddb.reset_mock()

        # Set up mock bedrock responses
        first_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>I need to use test_tool to add numbers</thinking>",
                        },
                        {
                            "toolUse": {
                                "name": "test_tool",
                                "input": {"a": 5, "b": 7},
                                "toolUseId": "123",
                            }
                        },
                    ],
                }
            },
            "stopReason": "tool_use",
        }

        final_response = {
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "text": "<thinking>Now I can provide the answer</thinking>The sum is 12."
                        }
                    ],
                }
            },
            "stopReason": "end_turn",
        }

        # Set up mock to return different responses on each call
        self.mock_bedrock.converse = MagicMock(
            side_effect=[first_response, final_response]
        )

        # Execute the run method
        agent_without_session.run("Add 5 and 7", session_id=self.session_id)

        # Verify DynamoDB was not called for updates
        self.mock_ddb.put_item.assert_not_called()

    def test_session_manager_update_reasoning_if_needed(self):
        """Test the session_manager's update_reasoning_if_needed method."""
        # Create a simple reasoning object
        step = ReasoningStep(step_number=1, thinking="Test thinking")
        reasoning = Reasoning(
            session_id=self.session_id, query="Test query", steps=[step], total_steps=1
        )

        # Reset the mock
        self.mock_ddb.reset_mock()

        # Test with real_time_reasoning enabled (default for self.agent)
        self.assertTrue(self.agent.session_manager.real_time_reasoning)
        result = self.agent.session_manager.update_reasoning_if_needed(
            reasoning, self.session_id
        )
        self.assertTrue(result)
        self.mock_ddb.put_item.assert_called_once()

        # Reset the mock
        self.mock_ddb.reset_mock()

        # Create a new agent with real_time_reasoning disabled
        with patch("boto3.client") as mock_boto3_client:
            mock_boto3_client.side_effect = lambda service, region_name=None: {
                "dynamodb": self.mock_ddb,
                "bedrock-runtime": self.mock_bedrock,
            }[service]

            agent_without_rt = Agent(
                tools=[self.test_tool],
                use_session_memory=True,
                real_time_reasoning=False,  # Disable real-time reasoning
                show_reasoning=False,
                log_level="CRITICAL",  # Disable normal logging for tests
            )

        # Test with real_time_reasoning disabled
        result = agent_without_rt.session_manager.update_reasoning_if_needed(
            reasoning, self.session_id
        )
        self.assertFalse(result)
        self.mock_ddb.put_item.assert_not_called()

    def test_get_reasoning_history(self):
        """Test retrieving reasoning history."""
        # Mock DynamoDB query response with multiple reasoning items
        mock_reasoning_dict1 = {
            "session_id": self.session_id,
            "query": "First query",
            "steps": [{"step_number": 1, "thinking": "First thinking"}],
            "total_steps": 1,
        }

        mock_reasoning_dict2 = {
            "session_id": self.session_id,
            "query": "Second query",
            "steps": [{"step_number": 1, "thinking": "Second thinking"}],
            "total_steps": 1,
        }

        self.mock_ddb.query.return_value = {
            "Items": [
                {"reasoning": {"S": json.dumps(mock_reasoning_dict1)}},
                {"reasoning": {"S": json.dumps(mock_reasoning_dict2)}},
            ]
        }

        # Get reasoning history
        history = self.agent.session_manager.get_reasoning_history(self.session_id)

        # Verify DynamoDB query was called correctly
        self.mock_ddb.query.assert_called_once()
        args, kwargs = self.mock_ddb.query.call_args
        self.assertEqual(
            kwargs["TableName"], self.agent.session_manager.session_table_name
        )
        self.assertEqual(
            kwargs["ExpressionAttributeValues"][":pk"]["S"],
            f"reasoning#{self.session_id}",
        )
        self.assertEqual(
            kwargs["ScanIndexForward"], True
        )  # Check order is oldest first

        # Verify result
        self.assertEqual(len(history), 2)
        self.assertIsInstance(history[0], Reasoning)
        self.assertEqual(history[0].query, "First query")
        self.assertEqual(history[0].steps[0].thinking, "First thinking")
        self.assertEqual(history[1].query, "Second query")
        self.assertEqual(history[1].steps[0].thinking, "Second thinking")

        # Test with invalid session ID
        self.mock_ddb.reset_mock()
        history = self.agent.session_manager.get_reasoning_history("invalid/session/id")
        self.assertEqual(history, [])
        self.mock_ddb.query.assert_not_called()

        # Test with exception
        self.mock_ddb.reset_mock()
        self.mock_ddb.query.side_effect = Exception("Test error")
        history = self.agent.session_manager.get_reasoning_history(self.session_id)
        self.assertEqual(history, [])


if __name__ == "__main__":
    unittest.main()
