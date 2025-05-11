"""Agent implementation for MinimalAgent."""

# Standard library imports
import datetime
import json
import re
import time
from textwrap import dedent
from typing import Any, Callable, Dict, List, Optional

# Third-party imports
import boto3
from botocore.exceptions import ClientError

# Local imports
from .utils.logging import Colors, color_log, setup_logging
from .utils.tools import create_tool_spec


class Agent:
    """
    A lightweight agent that uses Amazon Bedrock function calling API
    to process inputs and invoke appropriate tools.
    """

    def __init__(
        self,
        tools: Optional[List[Callable]] = None,
        max_steps: int = 5,
        show_reasoning: bool = True,
        model_id: str = "us.amazon.nova-pro-v1:0",
        bedrock_region: str = "us-west-2",
        memory_region: Optional[str] = None,
        system_prompt: str = "",
        use_session_memory: bool = False,
        session_table_name: str = "minimalagent-session-table",
        session_ttl: int = 3600,  # 1 hour default
    ):
        """
        Initialize the agent with configuration.

        Args:
            tools: Optional list of tool functions decorated with @tool
            max_steps: Maximum number of tool use iterations to allow
            show_reasoning: Whether to show agent's step-by-step reasoning process
            model_id: Amazon Bedrock model ID to use (default: us.amazon.nova-pro-v1:0)
            bedrock_region: AWS region for Bedrock (default: us-west-2)
            memory_region: AWS region for DynamoDB session storage (default: same as bedrock_region)
            system_prompt: System prompt to customize model behavior (default: empty string)
            use_session_memory: Whether to enable persistent session memory with DynamoDB (default: False)
            session_table_name: DynamoDB table name for storing session data (default: minimalagent-session-table)
            session_ttl: Time-to-live for session data in seconds (default: 3600 - 1 hour)
        """
        # Set up logging
        self.logger = setup_logging(show_reasoning)
        self.show_reasoning = show_reasoning

        # Set maximum tool use steps
        self.max_steps = max_steps

        # Set model and regions
        self.model_id = model_id
        self.system_prompt = system_prompt  # Will be processed before each run
        self.bedrock_region = bedrock_region
        self.memory_region = (
            memory_region if memory_region is not None else bedrock_region
        )

        # Session management settings
        # Enable session memory either explicitly or implicitly when a table name is provided
        self.use_session_memory = use_session_memory or (
            session_table_name != "minimalagent-session-table"
        )
        self.session_table_name = (
            session_table_name if self.use_session_memory else None
        )
        self.session_ttl = session_ttl
        self.ddb_client = None

        # Initialize session table if session memory is enabled (explicitly or implicitly)
        if self.use_session_memory:
            try:
                self.ddb_client = boto3.client(
                    "dynamodb", region_name=self.memory_region
                )
                self._ensure_session_table()
            except Exception as e:
                error_msg = f"Failed to initialize DynamoDB client: {str(e)}"
                if "Could not connect to the endpoint URL" in str(e):
                    error_msg = "AWS credentials not found or invalid. Please configure AWS credentials for DynamoDB access."
                elif "ExpiredToken" in str(e):
                    error_msg = "AWS credentials have expired. Please refresh your AWS credentials."

                self.logger.error(error_msg)
                self.use_session_memory = False
                self.session_table_name = None
                self.ddb_client = None

        # Initialize Bedrock client
        try:
            self.bedrock_client = boto3.client(
                "bedrock-runtime", region_name=self.bedrock_region
            )
        except Exception as e:
            error_msg = f"Failed to initialize Bedrock client: {str(e)}"
            if "Could not connect to the endpoint URL" in str(e):
                error_msg = "AWS credentials not found or invalid. Please configure AWS credentials for Amazon Bedrock access."
            elif "ExpiredToken" in str(e):
                error_msg = (
                    "AWS credentials have expired. Please refresh your AWS credentials."
                )

            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Initialize empty tool configuration
        self.tool_functions = {}
        self.tool_config = {"tools": []}

        # Process provided tools if any
        if tools:
            self.add_tools(tools)

    def _ensure_session_table(self):
        """
        Check if the DynamoDB table exists, and create it if it does not.
        """
        if not self.ddb_client:
            return

        try:
            # Check if table exists
            self.ddb_client.describe_table(TableName=self.session_table_name)
            if self.show_reasoning:
                self.logger.debug(
                    f"DynamoDB table {self.session_table_name} already exists."
                )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                # Create the table
                if self.show_reasoning:
                    self.logger.info(
                        f"Creating DynamoDB table {self.session_table_name}..."
                    )

                # Create the table without TTL first
                self.ddb_client.create_table(
                    TableName=self.session_table_name,
                    KeySchema=[
                        {
                            "AttributeName": "session_id",
                            "KeyType": "HASH",
                        },  # Partition key
                        {"AttributeName": "timestamp", "KeyType": "RANGE"},  # Sort key
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "session_id", "AttributeType": "S"},
                        {"AttributeName": "timestamp", "AttributeType": "N"},
                    ],
                    BillingMode="PAY_PER_REQUEST",
                )

                # Wait for table to be created
                waiter = self.ddb_client.get_waiter("table_exists")
                waiter.wait(TableName=self.session_table_name)

                # Enable TTL after table is created
                try:
                    self.ddb_client.update_time_to_live(
                        TableName=self.session_table_name,
                        TimeToLiveSpecification={
                            "AttributeName": "expiration_time",
                            "Enabled": True,
                        },
                    )
                except Exception as err:
                    self.logger.warning(
                        f"Failed to enable TTL on table, but table was created: {str(err)}"
                    )

                if self.show_reasoning:
                    self.logger.info(
                        f"DynamoDB table {self.session_table_name} created successfully."
                    )
            else:
                raise

    def _get_session_messages(self, session_id: str) -> List[Dict]:
        """
        Retrieve the most recent session messages from DynamoDB.

        Args:
            session_id: The session identifier

        Returns:
            List of message dictionaries if found, empty list otherwise
        """
        # Validate session_id to prevent injection attacks
        if (
            not self.ddb_client
            or not session_id
            or not self._is_valid_session_id(session_id)
        ):
            return []

        try:
            # Query the table to get the latest record for this session_id
            response = self.ddb_client.query(
                TableName=self.session_table_name,
                KeyConditionExpression="session_id = :sid",
                ExpressionAttributeValues={":sid": {"S": session_id}},
                ScanIndexForward=False,  # Sort in descending order (newest first)
                Limit=1,
            )

            if "Items" in response and response["Items"]:
                # Extract the messages JSON from the item
                item = response["Items"][0]
                if "messages" in item:
                    messages_json = item["messages"]["S"]
                    return json.loads(messages_json)

            if self.show_reasoning:
                self.logger.debug(
                    f"No existing messages found for session {session_id}"
                )

            return []

        except Exception as e:
            if self.show_reasoning:
                self.logger.error(f"Error retrieving session messages: {str(e)}")
            return []

    def _save_session_messages(self, session_id: str, messages: List[Dict]) -> bool:
        """
        Save the conversation messages to DynamoDB.

        Args:
            session_id: The session identifier
            messages: List of conversation message dictionaries

        Returns:
            True if successful, False otherwise
        """
        # Validate session_id to prevent injection attacks
        if (
            not self.ddb_client
            or not session_id
            or not messages
            or not self._is_valid_session_id(session_id)
        ):
            return False

        try:
            now = int(time.time())
            expiration_time = now + self.session_ttl

            # Store the messages as a JSON string
            messages_json = json.dumps(messages)

            # Save to DynamoDB
            self.ddb_client.put_item(
                TableName=self.session_table_name,
                Item={
                    "session_id": {"S": session_id},
                    "timestamp": {"N": str(now)},
                    "messages": {"S": messages_json},
                    "expiration_time": {"N": str(expiration_time)},
                },
            )

            if self.show_reasoning:
                self.logger.debug(f"Saved session messages for session {session_id}")

            return True

        except Exception as e:
            if self.show_reasoning:
                self.logger.error(f"Error saving session messages: {str(e)}")
            return False

    def add_tools(self, tools: List[Callable]):
        """
        Add tools to the agent

        Args:
            tools: List of tool functions decorated with @tool

        Returns:
            Self reference for chaining
        """
        tool_specs = []

        # Process each tool
        for tool in tools:
            # Ensure tool is decorated with @tool
            if not hasattr(tool, "tool_spec"):
                raise ValueError(
                    f"Function {tool.__name__} must be decorated with @tool"
                )

            name = tool.tool_spec["name"]

            # Add tool function to mapping
            self.tool_functions[name] = tool

            # Create tool spec
            tool_specs.append(create_tool_spec(name, tool))

        # Add tool specs to existing configuration
        self.tool_config["tools"].extend(tool_specs)

        return self

    def clear_tools(self):
        """
        Remove all tools from the agent

        Returns:
            Self reference for chaining
        """
        self.tool_functions = {}
        self.tool_config = {"tools": []}

        return self

    def _format_system_prompt(self) -> str:
        """
        Format the system prompt with current time and optional user instructions.

        Returns:
            Formatted system prompt string
        """
        # Add current UTC time
        current_time = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )

        # Create base prompt with just the time information
        system_prompt = dedent(
            f"""
            # General info
            - The current time and date in UTC is: {current_time}
            """
        ).strip()

        # Add user-provided prompt if any
        if self.system_prompt:
            system_prompt = f"{system_prompt}\n\n{self.system_prompt}"

        return system_prompt

    def _execute_tool(
        self, tool_name: str, tool_inputs: Dict, tool_use_id: str
    ) -> Dict:
        """
        Execute a tool and format the result for the API.

        Args:
            tool_name: Name of the tool to execute
            tool_inputs: Input parameters for the tool
            tool_use_id: Unique ID for this tool use

        Returns:
            Formatted tool result for the API
        """
        try:
            # Execute tool
            result = self.tool_functions[tool_name](**tool_inputs)

            if self.show_reasoning:
                # Log the result with color
                color_log(f"✓ {tool_name}:", Colors.GREEN)
                self.logger.info(json.dumps(result, indent=2))
                self.logger.info("")

            # Format for API
            return {
                "toolUseId": tool_use_id,
                "content": [{"json": result}],
            }

        except Exception as err:
            # Handle errors
            error_message = str(err)

            if self.show_reasoning:
                # Log the error with color
                color_log(f"✗ {tool_name} ERROR:", Colors.RED)
                color_log(f"Error: {error_message}", Colors.RED)
                self.logger.info(f"Inputs: {json.dumps(tool_inputs, indent=2)}")
                self.logger.info("")

            return {
                "toolUseId": tool_use_id,
                "content": [{"text": error_message}],
                "status": "error",
            }

    def _is_valid_session_id(self, session_id: str) -> bool:
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

    def run(self, input_text: str, session_id: Optional[str] = None) -> str:
        """
        Process user input, invoke tools if necessary, and return the response.
        Uses simple logging that creates a persistent log of each step.

        Args:
            input_text: The user's query/request
            session_id: Optional session identifier for persistent conversations.
                        Must contain only letters, numbers, underscores, and dashes,
                        and be 1-128 characters long.

        Returns:
            The agent's response
        """
        # Initialize messages - either from session or new conversation
        if self.use_session_memory and session_id:
            # Validate session ID format
            if not self._is_valid_session_id(session_id):
                error = "Invalid session_id format. Must contain only letters, numbers, underscores, dashes and be 1-128 characters."
                if self.show_reasoning:
                    self.logger.error(error)
                return error

            if self.ddb_client:
                # Try to load existing session
                messages = self._get_session_messages(session_id)
                if messages:
                    if self.show_reasoning:
                        self.logger.debug(
                            f"Loaded existing session {session_id} with {len(messages)} messages"
                        )
                else:
                    # New session with this ID
                    messages = []
                    if self.show_reasoning:
                        self.logger.debug(f"Starting new session with ID: {session_id}")

                # Add the new user message
                messages.append({"role": "user", "content": [{"text": input_text}]})
            else:
                # DynamoDB client not initialized or failed
                messages = [{"role": "user", "content": [{"text": input_text}]}]
        else:
            # No session tracking, just start with the user message
            messages = [{"role": "user", "content": [{"text": input_text}]}]

        step_count = 0

        if self.show_reasoning:
            # Print query with color - blank line before query
            self.logger.info("")
            color_log(f"QUERY: {input_text}", Colors.BOLD + Colors.CYAN)
            self.logger.info("")
            color_log("-" * 80, Colors.BLUE)

        try:
            # Get initial response from model
            converse_params = {
                "modelId": self.model_id,
                "messages": messages,
                "toolConfig": self.tool_config,
            }

            # Format and add system prompt
            full_system_prompt = self._format_system_prompt()
            converse_params["system"] = [{"text": full_system_prompt}]

            response = self.bedrock_client.converse(**converse_params)

            # Process steps
            while step_count < self.max_steps:
                output_message = response["output"]["message"]
                messages.append(output_message)
                stop_reason = response["stopReason"]

                # If model is done, exit the loop
                if stop_reason != "tool_use":
                    break

                # Increment step counter
                step_count += 1

                if self.show_reasoning:
                    # Log step header with color
                    self.logger.info("")
                    color_log(f"STEP {step_count}", Colors.BOLD + Colors.YELLOW)
                    color_log("-" * 40, Colors.YELLOW)

                # Process tool requests
                tool_requests = response["output"]["message"]["content"]
                tool_uses = [tr["toolUse"] for tr in tool_requests if "toolUse" in tr]
                tool_names = [tu["name"] for tu in tool_uses]

                # Extract and log thinking
                thinking = ""
                for content in tool_requests:
                    if (
                        "text" in content
                        and "<thinking>" in content["text"]
                        and "</thinking>" in content["text"]
                    ):
                        thinking_text = content["text"]
                        thinking = thinking_text[
                            thinking_text.find("<thinking>")
                            + 10 : thinking_text.find("</thinking>")
                        ].strip()

                if self.show_reasoning:
                    # Log the thinking/rationale with color
                    if thinking:
                        self.logger.info("")
                        color_log("RATIONALE:", Colors.BOLD)
                        self.logger.info(thinking)
                        self.logger.info("")

                    # Log the tools being called with color
                    if tool_uses:
                        color_log(f"ACTIONS ({len(tool_names)} tools):", Colors.BOLD)
                        for i, tool in enumerate(tool_uses, 1):
                            tool_name = tool["name"]
                            tool_inputs = (
                                json.dumps(tool["input"], indent=2)
                                if tool["input"]
                                else "{}"
                            )
                            self.logger.info(f"{i}. {tool_name}({tool_inputs})")
                        self.logger.info("")

                # Collect tool results for this step
                step_results = []

                if self.show_reasoning:
                    # Process each tool with color header
                    color_log("## TOOL RESULTS", Colors.BOLD + Colors.GREEN)
                    self.logger.info("")

                # Execute each tool
                for tool_request in tool_requests:
                    if "toolUse" in tool_request:
                        tool = tool_request["toolUse"]
                        tool_name = tool["name"]
                        tool_inputs = tool["input"]
                        tool_use_id = tool["toolUseId"]

                        if tool_name in self.tool_functions:
                            # Execute the tool and get result
                            tool_result = self._execute_tool(
                                tool_name, tool_inputs, tool_use_id
                            )
                            step_results.append({"toolResult": tool_result})

                # Send results back to model
                if step_results:
                    tool_result_message = {"role": "user", "content": step_results}
                    messages.append(tool_result_message)

                    if self.show_reasoning:
                        self.logger.info("-" * 40)

                    try:
                        converse_params = {
                            "modelId": self.model_id,
                            "messages": messages,
                            "toolConfig": self.tool_config,
                        }

                        # Format and add system prompt
                        full_system_prompt = self._format_system_prompt()
                        converse_params["system"] = [{"text": full_system_prompt}]

                        response = self.bedrock_client.converse(**converse_params)
                    except Exception as e:
                        error_msg = (
                            f"Error when sending tool results to model: {str(e)}"
                        )
                        if self.show_reasoning:
                            self.logger.error(error_msg)
                        raise Exception(error_msg)
                else:
                    # No tool results
                    if self.show_reasoning:
                        self.logger.info("Warning: No tool results were collected")
                    break

            # Check if we hit max steps
            if step_count == self.max_steps and response["stopReason"] == "tool_use":
                if self.show_reasoning:
                    self.logger.info("")
                    color_log(
                        f"! Maximum number of steps reached ({self.max_steps})",
                        Colors.RED + Colors.BOLD,
                    )
                    self.logger.info("")

                max_steps_message = {
                    "role": "user",
                    "content": [
                        {
                            "text": f"Maximum number of tool use iterations ({self.max_steps}) reached. Please provide a response with the information gathered so far."
                        }
                    ],
                }
                messages.append(max_steps_message)

                converse_params = {"modelId": self.model_id, "messages": messages}

                # Format and add system prompt
                full_system_prompt = self._format_system_prompt()
                converse_params["system"] = [{"text": full_system_prompt}]

                response = self.bedrock_client.converse(**converse_params)

            # Extract final response
            final_output = ""
            for content in response["output"]["message"]["content"]:
                if "text" in content:
                    final_output += content["text"] + "\n"

            # Check for thinking tags in final response
            if "<thinking>" in final_output and "</thinking>" in final_output:
                final_thinking = final_output[
                    final_output.find("<thinking>")
                    + 10 : final_output.find("</thinking>")
                ].strip()

                if self.show_reasoning:
                    self.logger.info("")
                    color_log("FINAL REASONING:", Colors.BOLD + Colors.YELLOW)
                    color_log("-" * 40, Colors.YELLOW)
                    self.logger.info(final_thinking)
                    self.logger.info("")

                clean_response = final_output.split("</thinking>")[-1].strip()
            else:
                clean_response = final_output.strip()

            if self.show_reasoning:
                # Print completion status
                self.logger.info("")
                color_log("-" * 80, Colors.BLUE)
                color_log(f"COMPLETE - {step_count} steps", Colors.GREEN + Colors.BOLD)
                self.logger.info("")

            # Pretty print the final response if reasoning display is enabled
            if self.show_reasoning:
                self.logger.info("")
                color_log("FINAL RESPONSE:", Colors.BOLD + Colors.GREEN)
                color_log("-" * 40, Colors.GREEN)
                print(clean_response)
                color_log("-" * 40, Colors.GREEN)

            # Save final conversation to DynamoDB if using session memory
            if self.use_session_memory and session_id and self.ddb_client:
                # Add final assistant message to the conversation history
                messages.append(response["output"]["message"])
                # Save to DynamoDB
                self._save_session_messages(session_id, messages)
                if self.show_reasoning:
                    self.logger.debug(
                        f"Saved conversation history for session {session_id}"
                    )

            return clean_response

        except Exception as e:
            error_message = f"Error while processing request: {str(e)}"

            # Format and display the error if reasoning display is enabled
            if self.show_reasoning:
                self.logger.info("")
                color_log("ERROR:", Colors.BOLD + Colors.RED)
                color_log("-" * 40, Colors.RED)
                print(error_message)
                color_log("-" * 40, Colors.RED)

            return error_message
