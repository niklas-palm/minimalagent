"""Tests for session continuity functionality."""

import json
from unittest.mock import MagicMock, patch

import pytest

from minimalagent import Agent
from minimalagent.models import Reasoning


class TestSessionContinuity:
    """Test cases for session continuity functionality."""

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
            {"role": "assistant", "content": [{"text": "First response"}]}
        ]
        
        # Mock DynamoDB to return existing messages
        mock_ddb_client.query.return_value = {
            "Items": [
                {
                    "pk": {"S": "messages#test_session"},
                    "sk": {"N": "1234567890"},
                    "messages": {"S": json.dumps(existing_messages)},
                    "expiration_time": {"N": "1234657890"}
                }
            ]
        }
        
        # Mock Bedrock response
        mock_bedrock_client.converse.return_value = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [{"text": "Second response"}]
                }
            }
        }
        
        # Create agent with session memory
        agent = Agent(use_session_memory=True, log_level="CRITICAL", show_reasoning=False)
        
        # Run agent with a new message
        response, reasoning = agent.run("Second message", session_id="test_session")
        
        # Verify that Bedrock was called with all messages
        mock_bedrock_client.converse.assert_called_once()
        call_args = mock_bedrock_client.converse.call_args[1]
        messages_sent = call_args["messages"]
        
        # Verify message history contains at least the original messages plus the new one
        assert len(messages_sent) >= 3  # At minimum 2 original + 1 new message
        
        # Find the original messages and new message in the array
        first_message_idx = next((i for i, m in enumerate(messages_sent) 
                              if m.get("role") == "user" and 
                              m.get("content")[0].get("text") == "First message"), None)
        
        first_response_idx = next((i for i, m in enumerate(messages_sent) 
                               if m.get("role") == "assistant" and 
                               m.get("content")[0].get("text") == "First response"), None)
                                   
        second_message_idx = next((i for i, m in enumerate(messages_sent) 
                               if m.get("role") == "user" and 
                               m.get("content")[0].get("text") == "Second message"), None)
        
        # Verify all required messages are present
        assert first_message_idx is not None, "First message not found"
        assert first_response_idx is not None, "First response not found"
        assert second_message_idx is not None, "Second message not found"
        
        # Verify the order of messages
        assert first_message_idx < first_response_idx < second_message_idx, "Messages are out of order"
        
        # Verify the new messages were saved back to DynamoDB
        mock_ddb_client.put_item.assert_called()
        
        # Find the put_item call that saves messages (not reasoning)
        message_save_call = None
        for call in mock_ddb_client.put_item.call_args_list:
            args, kwargs = call
            if "pk" in kwargs["Item"] and "messages#test_session" in str(kwargs["Item"]["pk"]["S"]):
                message_save_call = kwargs
                break
                
        assert message_save_call is not None
        
        # Verify the saved messages include the original + new message + new response
        if message_save_call:
            saved_messages_json = message_save_call["Item"]["messages"]["S"]
            saved_messages = json.loads(saved_messages_json)
            
            # Find the specific messages in the saved array
            first_message_saved = any(m.get("role") == "user" and 
                                   m.get("content")[0].get("text") == "First message" 
                                   for m in saved_messages)
                                   
            first_response_saved = any(m.get("role") == "assistant" and 
                                    m.get("content")[0].get("text") == "First response" 
                                    for m in saved_messages)
                                    
            second_message_saved = any(m.get("role") == "user" and 
                                    m.get("content")[0].get("text") == "Second message" 
                                    for m in saved_messages)
                                    
            second_response_saved = any(m.get("role") == "assistant" and 
                                     m.get("content")[0].get("text") == "Second response" 
                                     for m in saved_messages)
            
            # Verify all required messages are present in saved data
            assert first_message_saved, "First message not saved"
            assert first_response_saved, "First response not saved"
            assert second_message_saved, "Second message not saved" 
            assert second_response_saved, "Second response not saved"
        else:
            assert False, "No message save call found in DynamoDB put_item calls"