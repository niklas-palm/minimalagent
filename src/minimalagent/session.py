"""Session management functionality for MinimalAgent."""

# Standard library imports
import json
import re
import time
from typing import Any, Dict, List, Optional, Union

# Third-party imports
import boto3
from botocore.exceptions import ClientError

# Local imports
from .models import Reasoning, ReasoningStep, ToolData


class SessionManager:
    """
    Manages session persistence and retrieval using DynamoDB.
    Handles conversation history and reasoning data storage.
    """

    def __init__(
        self,
        logger,
        use_session_memory: bool = False,
        session_table_name: str = "minimalagent-session-table",
        memory_region: str = "us-west-2",
        session_ttl: int = 3600,
        show_reasoning: bool = True,
        real_time_reasoning: bool = False,
    ):
        """
        Initialize the session manager.

        Args:
            logger: Logger instance for logging messages
            use_session_memory: Whether to enable session persistence
            session_table_name: DynamoDB table name for storing session data
            memory_region: AWS region for DynamoDB
            session_ttl: Time-to-live for session data in seconds
            show_reasoning: Whether to show agent's reasoning process
        """
        self.logger = logger
        self.use_session_memory = use_session_memory
        self.session_table_name = session_table_name if use_session_memory else None
        self.memory_region = memory_region
        self.session_ttl = session_ttl
        self.show_reasoning = show_reasoning
        self.real_time_reasoning = real_time_reasoning and use_session_memory

        # Log warning if real-time reasoning was disabled due to session memory being disabled
        if real_time_reasoning and not use_session_memory:
            logger.warning(
                "real_time_reasoning requires use_session_memory=True, disabling real-time reasoning"
            )

        self.ddb_client = None

        if use_session_memory:
            self._initialize_dynamodb()

    def _initialize_dynamodb(self) -> None:
        """Initialize the DynamoDB client and ensure the session table exists."""
        try:
            self.ddb_client = boto3.client("dynamodb", region_name=self.memory_region)
            self.ensure_session_table()
        except ClientError as e:
            # Handle specific boto3 client errors
            error_code = e.response.get("Error", {}).get("Code", "")

            if error_code == "UnrecognizedClientException":
                error_msg = "Invalid AWS credentials. Please configure valid AWS credentials for DynamoDB access."
            elif error_code == "ExpiredTokenException":
                error_msg = (
                    "AWS credentials have expired. Please refresh your AWS credentials."
                )
            elif error_code == "AccessDeniedException" or error_code == "AccessDenied":
                error_msg = "Insufficient permissions to access DynamoDB. Check your IAM permissions."
            elif error_code == "InvalidSignatureException":
                error_msg = "Invalid AWS signature. Check your AWS credentials and region configuration."
            else:
                error_msg = f"DynamoDB client error ({error_code}): {str(e)}"

            self.logger.error(error_msg)
            self.use_session_memory = False
            self.session_table_name = None
            self.ddb_client = None
        except Exception as e:
            error_msg = f"Failed to initialize DynamoDB client: {str(e)}"
            if "Could not connect to the endpoint URL" in str(e):
                error_msg = (
                    f"Could not connect to DynamoDB in region {self.memory_region}. "
                    "Please check your internet connection and AWS region configuration."
                )

            self.logger.error(error_msg)
            self.use_session_memory = False
            self.session_table_name = None
            self.ddb_client = None

    def ensure_session_table(self) -> bool:
        """
        Create the DynamoDB table for session data if it doesn't exist.

        Returns:
            bool: True if the table exists or was created, False otherwise
        """
        if not self.ddb_client or not self.session_table_name:
            return False

        try:
            try:
                self.ddb_client.describe_table(TableName=self.session_table_name)
                self.logger.info(
                    f"Session table {self.session_table_name} already exists"
                )
                return True
            except ClientError as e:
                if e.response["Error"]["Code"] != "ResourceNotFoundException":
                    self.logger.error(
                        f"Error checking session table existence: {str(e)}"
                    )
                    self.use_session_memory = False
                    self.session_table_name = None
                    return False

                self.logger.info(f"Creating session table {self.session_table_name}")

                try:
                    self.ddb_client.create_table(
                        TableName=self.session_table_name,
                        KeySchema=[
                            {
                                "AttributeName": "pk",
                                "KeyType": "HASH",
                            },  # Partition key
                            {"AttributeName": "sk", "KeyType": "RANGE"},  # Sort key
                        ],
                        AttributeDefinitions=[
                            {"AttributeName": "pk", "AttributeType": "S"},
                            {"AttributeName": "sk", "AttributeType": "N"},
                        ],
                        BillingMode="PAY_PER_REQUEST",
                    )
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code == "LimitExceededException":
                        self.logger.error(
                            "DynamoDB table limit exceeded for this account. Consider deleting unused tables."
                        )
                        raise RuntimeError(
                            "DynamoDB table limit exceeded for this account."
                        )
                    elif (
                        error_code == "AccessDeniedException"
                        or error_code == "AccessDenied"
                    ):
                        self.logger.error(
                            "Insufficient permissions to create DynamoDB table. Check your IAM permissions."
                        )
                        self.use_session_memory = False
                        self.session_table_name = None
                        return False
                    else:
                        self.logger.error(
                            f"Failed to create DynamoDB table: {error_code} - {str(e)}"
                        )
                        self.use_session_memory = False
                        self.session_table_name = None
                        return False

                # Wait for table to be created
                waiter = self.ddb_client.get_waiter("table_exists")
                waiter.wait(TableName=self.session_table_name)
                self.logger.info(
                    f"Table {self.session_table_name} created successfully"
                )

            # Enable TTL on the table
            try:
                self.ddb_client.update_time_to_live(
                    TableName=self.session_table_name,
                    TimeToLiveSpecification={
                        "Enabled": True,
                        "AttributeName": "expiration_time",
                    },
                )
                self.logger.info(f"TTL enabled for table {self.session_table_name}")
            except ClientError as e:
                # TTL errors are non-fatal, just log it
                self.logger.error(f"Failed to enable TTL on session table: {str(e)}")

            return True

        except Exception as e:
            self.logger.error(f"Error ensuring session table exists: {str(e)}")
            self.use_session_memory = False
            self.session_table_name = None
            return False

    def is_valid_session_id(self, session_id: str) -> bool:
        """
        Validate session ID to prevent injection attacks.

        Args:
            session_id: The session identifier to validate

        Returns:
            True if session_id is valid, False otherwise
        """
        # Session ID must not be empty and should only contain alphanumeric chars,
        # dashes, underscores, and can be up to 128 chars (common DynamoDB constraints)
        if not session_id:
            return False

        # Validate using regex pattern for safe characters
        pattern = r"^[a-zA-Z0-9_\-]{1,128}$"
        return bool(re.match(pattern, session_id))

    def is_valid_table_name(self, table_name: str) -> bool:
        """
        Validate DynamoDB table name according to AWS naming rules.

        Args:
            table_name: The table name to validate

        Returns:
            True if table_name is valid, False otherwise
        """
        # Table name must be 3-255 characters long and contain only the following:
        # a-z, A-Z, 0-9, _ (underscore), - (dash), and . (dot)
        if not table_name:
            return False

        if len(table_name) < 3 or len(table_name) > 255:
            return False

        # AWS DynamoDB table name validation regex
        pattern = r"^[a-zA-Z0-9_\-.]+$"
        return bool(re.match(pattern, table_name))

    def get_session_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the most recent conversation history for a session from DynamoDB.

        Args:
            session_id: The session identifier

        Returns:
            List of message objects in the conversation
        """
        # Validate session_id to prevent injection attacks
        if (
            not self.ddb_client
            or not session_id
            or not self.is_valid_session_id(session_id)
        ):
            return []

        try:
            # Query the table to get the most recent message item for this session_id
            response = self.ddb_client.query(
                TableName=self.session_table_name,
                KeyConditionExpression="pk = :pk",
                ExpressionAttributeValues={":pk": {"S": f"messages#{session_id}"}},
                ScanIndexForward=False,  # Sort in descending order (newest first)
                Limit=1,  # Only get the most recent item
            )

            messages = []
            if "Items" in response and response["Items"]:
                item = response["Items"][0]  # Get the first (most recent) item
                if "messages" in item:
                    message_json = item["messages"]["S"]
                    return json.loads(message_json)

            return messages

        except Exception as e:
            self.logger.error(f"Error retrieving session messages: {str(e)}")
            return []

    def save_session_messages(
        self, session_id: str, messages: List[Dict[str, Any]]
    ) -> bool:
        """
        Save conversation history to DynamoDB.
        Simply overwrites the current session messages with the new ones.

        Args:
            session_id: The session identifier
            messages: List of message objects to save

        Returns:
            True if successful, False otherwise
        """
        if not self.ddb_client:
            return False

        if not session_id or not self.is_valid_session_id(session_id):
            return False

        try:
            # Save messages directly as a new item, overwriting any existing data
            timestamp = int(time.time())
            expiration_time = timestamp + self.session_ttl

            self.ddb_client.put_item(
                TableName=self.session_table_name,
                Item={
                    "pk": {"S": f"messages#{session_id}"},
                    "sk": {"N": str(timestamp)},
                    "message_count": {"N": str(len(messages))},
                    "messages": {"S": json.dumps(messages)},
                    "expiration_time": {"N": str(expiration_time)},
                },
            )

            return True

        except Exception as e:
            self.logger.error(f"Error saving session messages: {str(e)}")
            return False

    def update_reasoning(
        self,
        reasoning: Optional[Reasoning] = None,
        thinking: Optional[str] = None,
        tool_data: Optional[List] = None,
        step_number: int = 0,
        timestamp: Optional[int] = None,
    ) -> Reasoning:
        """
        Update the reasoning object with new information about the current step.

        Args:
            reasoning: The current reasoning object to update
            thinking: The thinking/rationale text for this step
            tool_data: List of tool usage data (name, inputs, results)
            step_number: The current step number
            timestamp: The timestamp for this step

        Returns:
            The updated reasoning object
        """
        # Initialize reasoning object if needed
        if reasoning is None:
            reasoning = Reasoning()

        # Only add step if there's actual content
        if thinking or tool_data:
            # Create tools list if tool data is provided
            tools = []
            if tool_data:
                for tool in tool_data:
                    tools.append(
                        ToolData(
                            name=tool.get("name", ""),
                            inputs=tool.get("inputs", {}),
                            result=tool.get("result", None),
                        )
                    )

            # Create the reasoning step
            step = ReasoningStep(
                step_number=step_number,
                timestamp=timestamp or int(time.time()),
                thinking=thinking,
                tools=tools,
            )

            # Add step to reasoning object
            reasoning.steps.append(step)
            reasoning.total_steps = len(reasoning.steps)

        return reasoning

    def update_reasoning_if_needed(self, reasoning: Reasoning, session_id: str) -> bool:
        """
        Update reasoning data in real-time if real-time reasoning is enabled.

        Args:
            reasoning: Current reasoning object
            session_id: Session identifier

        Returns:
            True if reasoning was updated, False otherwise
        """
        # Only save if real-time reasoning and session memory are both enabled
        if (
            self.use_session_memory
            and self.real_time_reasoning
            and self.ddb_client
            and session_id
        ):
            # Save reasoning data to DynamoDB
            return self.save_reasoning_data(session_id, reasoning)
        return False

    def get_reasoning(self, session_id: str) -> Reasoning:
        """
        Retrieve reasoning data for the most recent interaction in a session.

        Args:
            session_id: The session identifier

        Returns:
            Reasoning object containing reasoning data or empty Reasoning if not found
        """
        # Validate session_id to prevent injection attacks
        if (
            not self.ddb_client
            or not session_id
            or not self.is_valid_session_id(session_id)
        ):
            return Reasoning()

        try:
            # Query the table to get the most recent reasoning for this session_id
            response = self.ddb_client.query(
                TableName=self.session_table_name,
                KeyConditionExpression="pk = :pk",
                ExpressionAttributeValues={":pk": {"S": f"reasoning#{session_id}"}},
                ScanIndexForward=False,  # Sort in descending order (newest first)
                Limit=1,  # Only get the most recent
            )

            if "Items" in response and response["Items"]:
                item = response["Items"][0]
                if "reasoning" in item:
                    reasoning_json = item["reasoning"]["S"]
                    reasoning_dict = json.loads(reasoning_json)
                    return Reasoning.from_dict(reasoning_dict)

            return Reasoning()

        except Exception as e:
            self.logger.error(f"Error retrieving reasoning data: {str(e)}")
            return Reasoning()

    def get_reasoning_history(self, session_id: str) -> List[Reasoning]:
        """
        Retrieve all reasoning objects for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of reasoning objects ordered by timestamp
        """
        # Validate session_id to prevent injection attacks
        if (
            not self.ddb_client
            or not session_id
            or not self.is_valid_session_id(session_id)
        ):
            return []

        try:
            # Query the table to get all records for this session_id
            response = self.ddb_client.query(
                TableName=self.session_table_name,
                KeyConditionExpression="pk = :pk",
                ExpressionAttributeValues={":pk": {"S": f"reasoning#{session_id}"}},
                ScanIndexForward=True,  # Sort in ascending order (oldest first)
            )

            reasoning_history = []
            if "Items" in response:
                for item in response["Items"]:
                    if "reasoning" in item:
                        reasoning_json = item["reasoning"]["S"]
                        reasoning_dict = json.loads(reasoning_json)
                        reasoning_history.append(Reasoning.from_dict(reasoning_dict))

            return reasoning_history

        except Exception as e:
            self.logger.error(f"Error retrieving reasoning history: {str(e)}")
            return []

    def _truncate_reasoning(self, reasoning: Reasoning) -> Reasoning:
        """
        Truncate reasoning data to fit within DynamoDB capacity limits.

        Args:
            reasoning: The reasoning data to truncate

        Returns:
            Truncated reasoning data
        """
        if len(reasoning.steps) <= 2:
            return reasoning

        # Create a new reasoning object with only first and last steps
        truncated = Reasoning(
            session_id=reasoning.session_id,
            query=reasoning.query,
            steps=[reasoning.steps[0], reasoning.steps[-1]],
            total_steps=reasoning.total_steps,
            final_response=reasoning.final_response,
            final_thinking=reasoning.final_thinking,
            truncated=True,
            exceeded_size_limit=reasoning.exceeded_size_limit,
        )

        return truncated

    def _serialize_reasoning(self, reasoning: Reasoning) -> str:
        """
        Serialize reasoning data to JSON.

        Args:
            reasoning: The reasoning data to serialize

        Returns:
            JSON string of reasoning data

        Raises:
            Exception: If serialization fails
        """
        # Convert to dictionary first
        reasoning_dict = reasoning.to_dict()
        reasoning_json = json.dumps(reasoning_dict)
        return reasoning_json

    def save_reasoning_data(self, session_id: str, reasoning: Reasoning) -> bool:
        """
        Save reasoning data to DynamoDB.

        Args:
            session_id: The session identifier
            reasoning: Reasoning object containing reasoning data

        Returns:
            True if successful, False otherwise
        """
        # Validate session_id and client
        if not self.ddb_client:
            return False

        if not session_id or not self.is_valid_session_id(session_id):
            return False

        try:
            # Make sure session_id is set in the reasoning object
            if not reasoning.session_id:
                reasoning.session_id = session_id

            # Serialize reasoning data
            try:
                reasoning_json = self._serialize_reasoning(reasoning)
            except Exception as e:
                self.logger.error(f"Error serializing reasoning data: {str(e)}")
                return False

            timestamp = int(time.time())
            expiration_time = timestamp + self.session_ttl

            try:
                # Try to save the full reasoning data
                self.ddb_client.put_item(
                    TableName=self.session_table_name,
                    Item={
                        "pk": {"S": f"reasoning#{session_id}"},
                        "sk": {"N": str(timestamp)},
                        "reasoning": {"S": reasoning_json},
                        "expiration_time": {"N": str(expiration_time)},
                    },
                )
                return True

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                error_msg = e.response.get("Error", {}).get("Message", "")

                # Check if this is a size limit error
                if (
                    "size exceeds" in error_msg.lower()
                    or error_code == "ItemSizeTooLarge"
                ):
                    self.logger.error(
                        f"Reasoning data exceeds DynamoDB's capacity limit: {error_msg}"
                    )

                    # Update the reasoning object to indicate size limit was exceeded
                    reasoning.exceeded_size_limit = True

                    # Add warning to final response if it exists
                    size_limit_warning = "\n\nWARNING: This reasoning process was interrupted because it exceeded the maximum size limit for persistence. Some details may be missing."

                    if reasoning.final_response:
                        if size_limit_warning not in reasoning.final_response:
                            reasoning.final_response += size_limit_warning

                    # Try to save a truncated version with just enough information to be useful
                    truncated_reasoning = self._truncate_reasoning(reasoning)
                    truncated_json = json.dumps(truncated_reasoning.to_dict())

                    try:
                        self.ddb_client.put_item(
                            TableName=self.session_table_name,
                            Item={
                                "pk": {"S": f"reasoning#{session_id}"},
                                "sk": {"N": str(timestamp)},
                                "reasoning": {"S": truncated_json},
                                "expiration_time": {"N": str(expiration_time)},
                            },
                        )
                        # We succeeded in saving the truncated version
                        return True
                    except Exception:
                        # Even truncated version failed
                        self.logger.error(
                            "Failed to save even truncated reasoning data"
                        )
                        return False
                else:
                    # Some other DynamoDB error
                    self.logger.error(f"Error saving reasoning data: {error_msg}")
                    return False

        except Exception as e:
            self.logger.error(f"Error saving reasoning data: {str(e)}")
            return False
