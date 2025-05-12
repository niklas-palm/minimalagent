"""Tests for session continuity functionality."""

import json
from unittest.mock import MagicMock, patch

import pytest

from minimalagent import Agent, tool
from minimalagent.models import Reasoning


class TestSessionContinuity:
    """Test cases for session continuity functionality."""

    @tool
    def calculate(a: int, b: int):
        """Add two numbers together.

        Args:
            a: First number
            b: Second number

        Returns:
            Sum of the two numbers
        """
        return {"result": a + b}

    @patch("minimalagent.agent.boto3")
    @patch("minimalagent.session.boto3")
    def test_session_continuity(self, mock_session_boto3, mock_agent_boto3):
        """Test that agent retrieves existing messages and continues the conversation."""
        # Set up mock clients
        mock_bedrock_client = MagicMock()
        mock_ddb_client = MagicMock()

        # Configure boto3 mocks
        mock_agent_boto3.client.return_value = mock_bedrock_client
        mock_session_boto3.client.return_value = mock_ddb_client

        # Create existing messages for the session
        existing_messages = [
            {"role": "user", "content": [{"text": "First message"}]},
            {"role": "assistant", "content": [{"text": "First response"}]},
        ]

        # Mock DynamoDB to return existing messages
        mock_ddb_client.query.return_value = {
            "Items": [
                {
                    "pk": {"S": "messages#test_session"},
                    "sk": {"N": "1234567890"},
                    "messages": {"S": json.dumps(existing_messages)},
                    "expiration_time": {"N": "1234657890"},
                }
            ]
        }

        # Mock Bedrock response
        mock_bedrock_client.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Second response"}],
                }
            },
        }

        # Create agent with session memory
        agent = Agent(
            use_session_memory=True, log_level="CRITICAL", show_reasoning=False
        )

        # Run agent with a new message
        response, reasoning = agent.run("Second message", session_id="test_session")

        # Verify that Bedrock was called with all messages
        mock_bedrock_client.converse.assert_called_once()
        call_args = mock_bedrock_client.converse.call_args[1]
        messages_sent = call_args["messages"]

        # Verify message history contains at least the original messages plus the new one
        assert len(messages_sent) >= 3  # At minimum 2 original + 1 new message

        # Find the original messages and new message in the array
        first_message_idx = next(
            (
                i
                for i, m in enumerate(messages_sent)
                if m.get("role") == "user"
                and m.get("content")[0].get("text") == "First message"
            ),
            None,
        )

        first_response_idx = next(
            (
                i
                for i, m in enumerate(messages_sent)
                if m.get("role") == "assistant"
                and m.get("content")[0].get("text") == "First response"
            ),
            None,
        )

        second_message_idx = next(
            (
                i
                for i, m in enumerate(messages_sent)
                if m.get("role") == "user"
                and m.get("content")[0].get("text") == "Second message"
            ),
            None,
        )

        # Verify all required messages are present
        assert first_message_idx is not None, "First message not found"
        assert first_response_idx is not None, "First response not found"
        assert second_message_idx is not None, "Second message not found"

        # Verify the order of messages
        assert (
            first_message_idx < first_response_idx < second_message_idx
        ), "Messages are out of order"

        # Verify the new messages were saved back to DynamoDB
        mock_ddb_client.put_item.assert_called()

        # Find the put_item call that saves messages (not reasoning)
        message_save_call = None
        for call in mock_ddb_client.put_item.call_args_list:
            args, kwargs = call
            if "pk" in kwargs["Item"] and "messages#test_session" in str(
                kwargs["Item"]["pk"]["S"]
            ):
                message_save_call = kwargs
                break

        assert message_save_call is not None

        # Verify the saved messages include the original + new message + new response
        if message_save_call:
            saved_messages_json = message_save_call["Item"]["messages"]["S"]
            saved_messages = json.loads(saved_messages_json)

            # Find the specific messages in the saved array
            first_message_saved = any(
                m.get("role") == "user"
                and m.get("content")[0].get("text") == "First message"
                for m in saved_messages
            )

            first_response_saved = any(
                m.get("role") == "assistant"
                and m.get("content")[0].get("text") == "First response"
                for m in saved_messages
            )

            second_message_saved = any(
                m.get("role") == "user"
                and m.get("content")[0].get("text") == "Second message"
                for m in saved_messages
            )

            second_response_saved = any(
                m.get("role") == "assistant"
                and m.get("content")[0].get("text") == "Second response"
                for m in saved_messages
            )

            # Verify all required messages are present in saved data
            assert first_message_saved, "First message not saved"
            assert first_response_saved, "First response not saved"
            assert second_message_saved, "Second message not saved"
            assert second_response_saved, "Second response not saved"
        else:
            assert False, "No message save call found in DynamoDB put_item calls"

    @patch("minimalagent.agent.boto3")
    @patch("minimalagent.session.boto3")
    def test_session_tool_continuity(self, mock_session_boto3, mock_agent_boto3):
        """Test session continuity with tool use."""
        # Set up mock clients
        mock_bedrock_client = MagicMock()
        mock_ddb_client = MagicMock()

        # Configure boto3 mocks
        mock_agent_boto3.client.return_value = mock_bedrock_client
        mock_session_boto3.client.return_value = mock_ddb_client

        # Create existing messages for the session with previous tool use
        existing_messages = [
            {"role": "user", "content": [{"text": "Add 5 and 3"}]},
            {
                "role": "assistant",
                "content": [
                    {"text": "I'll help you add those numbers."},
                    {
                        "toolUse": {
                            "name": "calculate",
                            "input": {"a": 5, "b": 3},
                            "toolUseId": "prev123",
                        }
                    },
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "toolResult": {
                            "toolUseId": "prev123",
                            "content": [{"json": {"result": 8}}],
                        }
                    }
                ],
            },
            {"role": "assistant", "content": [{"text": "The result is 8."}]},
        ]

        # Mock DynamoDB to return existing messages
        mock_ddb_client.query.return_value = {
            "Items": [
                {
                    "pk": {"S": "messages#test_session"},
                    "sk": {"N": "1234567890"},
                    "messages": {"S": json.dumps(existing_messages)},
                    "expiration_time": {"N": "1234657890"},
                }
            ]
        }

        # Set up two responses for the mock:
        # 1. First response requesting tool use
        tool_response = {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "I'll help you add those numbers together."},
                        {
                            "toolUse": {
                                "name": "calculate",
                                "input": {"a": 10, "b": 7},
                                "toolUseId": "new456",
                            }
                        },
                    ],
                }
            },
        }

        # 2. Final response after tool execution
        final_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "The result of 10 + 7 is 17."}],
                }
            },
        }

        # Configure mock to return different responses on successive calls
        mock_bedrock_client.converse.side_effect = [tool_response, final_response]

        # Create agent with the tool and session memory
        agent = Agent(
            tools=[self.calculate],
            use_session_memory=True,
            log_level="CRITICAL",
            show_reasoning=False,
        )

        # Run agent with a new calculation request
        response, reasoning = agent.run("Add 10 and 7", session_id="test_session")

        # 1. Verify previous session messages were loaded
        assert mock_ddb_client.query.call_count > 0

        # 2. Verify first model call contained previous conversation history
        first_call_args = mock_bedrock_client.converse.call_args_list[0][1]
        first_messages = first_call_args["messages"]

        # Check for previous calculation in the message history
        prev_calculation_request = any(
            m.get("role") == "user"
            and any(
                "Add 5 and 3" in str(c.get("text", "")) for c in m.get("content", [])
            )
            for m in first_messages
        )
        assert (
            prev_calculation_request
        ), "Previous calculation request not found in messages"

        # Check for previous tool use in the message history
        prev_tool_use = any(
            m.get("role") == "assistant"
            and any(tu for tu in m.get("content", []) if "toolUse" in tu)
            for m in first_messages
        )
        assert prev_tool_use, "Previous tool use not found in messages"

        # Check for previous tool result in the message history
        prev_tool_result = any(
            m.get("role") == "user"
            and any(tr for tr in m.get("content", []) if "toolResult" in tr)
            for m in first_messages
        )
        assert prev_tool_result, "Previous tool result not found in messages"

        # 3. Verify new tool was invoked
        assert (
            len(mock_bedrock_client.converse.call_args_list) >= 2
        ), "Model should be called at least twice"

        # 4. Verify second model call contained tool results
        second_call_args = mock_bedrock_client.converse.call_args_list[1][1]
        second_messages = second_call_args["messages"]

        # Find tool result in the messages
        new_tool_result = any(
            m.get("role") == "user"
            and any(
                tr
                for tr in m.get("content", [])
                if "toolResult" in tr and tr["toolResult"].get("toolUseId") == "new456"
            )
            for m in second_messages
        )
        assert new_tool_result, "New tool result not found in messages sent to model"

        # 5. Verify complete history saved to DynamoDB
        put_item_calls = [
            c
            for c in mock_ddb_client.put_item.call_args_list
            if "pk" in c[1]["Item"]
            and "messages#test_session" in str(c[1]["Item"]["pk"]["S"])
        ]
        assert len(put_item_calls) > 0, "No message save calls found"

        # Get the saved messages from the last put_item call
        last_save_call = put_item_calls[-1]
        saved_messages_json = last_save_call[1]["Item"]["messages"]["S"]
        saved_messages = json.loads(saved_messages_json)

        # Verify previous calculation is present
        prev_calc_saved = any(
            m.get("role") == "user"
            and any(
                "Add 5 and 3" in str(c.get("text", "")) for c in m.get("content", [])
            )
            for m in saved_messages
        )
        assert prev_calc_saved, "Previous calculation not found in saved messages"

        # Verify new calculation is present
        new_calc_saved = any(
            m.get("role") == "user"
            and any(
                "Add 10 and 7" in str(c.get("text", "")) for c in m.get("content", [])
            )
            for m in saved_messages
        )
        assert new_calc_saved, "New calculation not found in saved messages"

        # Verify new tool use is present
        new_tool_use_saved = any(
            m.get("role") == "assistant"
            and any(
                tu
                for tu in m.get("content", [])
                if "toolUse" in tu and tu["toolUse"].get("toolUseId") == "new456"
            )
            for m in saved_messages
        )
        assert new_tool_use_saved, "New tool use not found in saved messages"

        # Verify new tool result is present
        new_tool_result_saved = any(
            m.get("role") == "user"
            and any(
                tr
                for tr in m.get("content", [])
                if "toolResult" in tr and tr["toolResult"].get("toolUseId") == "new456"
            )
            for m in saved_messages
        )
        assert new_tool_result_saved, "New tool result not found in saved messages"

        # Verify final response is present
        final_response_saved = any(
            m.get("role") == "assistant"
            and any("17" in str(c.get("text", "")) for c in m.get("content", []))
            for m in saved_messages
        )
        assert final_response_saved, "Final response not found in saved messages"
