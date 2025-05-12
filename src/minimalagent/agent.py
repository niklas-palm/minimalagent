"""Agent implementation for MinimalAgent."""

# Standard library imports
import datetime
import json
from textwrap import dedent
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Third-party imports
import boto3
from botocore.exceptions import ClientError

from .models import Reasoning, ReasoningStep, ToolData
from .session import SessionManager

# Local imports
from .utils.logging import setup_logging
from .utils.reasoning_display import ReasoningDisplay
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
        log_level: str = "WARNING",
        model_id: str = "us.amazon.nova-pro-v1:0",
        bedrock_region: str = "us-west-2",
        memory_region: Optional[str] = None,
        system_prompt: str = "",
        use_session_memory: bool = False,
        real_time_reasoning: bool = False,
        session_table_name: str = "minimalagent-session-table",
        session_ttl: int = 3600,  # 1 hour default
    ):
        """
        Initialize the agent with configuration.

        Args:
            tools: Optional list of tool functions decorated with @tool
            max_steps: Maximum number of tool use iterations to allow (must be > 0)
            show_reasoning: Whether to show agent's step-by-step reasoning process with color formatting
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            model_id: Amazon Bedrock model ID to use (default: us.amazon.nova-pro-v1:0)
            bedrock_region: AWS region for Bedrock (default: us-west-2)
            memory_region: AWS region for DynamoDB session storage (default: same as bedrock_region)
            system_prompt: System prompt to customize model behavior (default: empty string)
            use_session_memory: Whether to enable persistent session memory with DynamoDB (default: False)
            real_time_reasoning: Whether to update reasoning in real-time during execution (default: False)
            session_table_name: DynamoDB table name for storing session data (default: minimalagent-session-table)
            session_ttl: Time-to-live for session data in seconds (must be > 0, default: 3600 - 1 hour)

        Raises:
            ValueError: If max_steps <= 0, session_ttl <= 0, or invalid log_level
            ValueError: If session_table_name contains invalid characters
            ValueError: If tools contains functions not decorated with @tool
        """
        # Validate parameters
        self._validate_param(max_steps > 0, "max_steps must be greater than 0")
        self._validate_param(session_ttl > 0, "session_ttl must be greater than 0")

        # Validate table name if provided
        if session_table_name:
            temp_manager = SessionManager(logger=setup_logging(False, "WARNING"))
            self._validate_param(
                temp_manager.is_valid_table_name(session_table_name),
                "session_table_name must contain only alphanumeric characters, hyphens, dots, and underscores, "
                "and be between 3 and 255 characters in length",
            )

        # Set up logging with separate controls for reasoning display and log level
        self.logger = setup_logging(show_reasoning, log_level)
        self.show_reasoning = show_reasoning

        # Set up reasoning display
        self.display = ReasoningDisplay(self.logger) if show_reasoning else None

        # Store basic configuration
        self.max_steps = max_steps
        self.model_id = model_id
        self.system_prompt = system_prompt  # Will be processed before each run
        self.bedrock_region = bedrock_region

        # Auto-enable session memory if a custom table name is provided
        use_session_memory = use_session_memory or (
            session_table_name != "minimalagent-session-table"
        )

        # Initialize session manager with validation and DynamoDB handling
        memory_region_to_use = (
            memory_region if memory_region is not None else bedrock_region
        )
        self.session_manager = SessionManager(
            logger=self.logger,
            use_session_memory=use_session_memory,
            session_table_name=session_table_name,
            memory_region=memory_region_to_use,
            session_ttl=session_ttl,
            show_reasoning=show_reasoning,
            real_time_reasoning=real_time_reasoning,
        )

        try:
            self.bedrock_client = boto3.client(
                "bedrock-runtime", region_name=self.bedrock_region
            )
        except ClientError as e:
            error_msg = self._get_aws_error_message(e, "Bedrock")
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = self._get_general_error_message(
                e, "Bedrock", self.bedrock_region
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

        self.tool_functions = {}
        self.tool_config = {"tools": []}
        if tools:
            try:
                self.add_tools(tools)
            except (TypeError, ValueError) as e:
                self.logger.error(f"Failed to initialize tools: {str(e)}")
                raise ValueError(f"Invalid tools parameter: {str(e)}")

    def get_reasoning(self, session_id: str) -> Reasoning:
        """
        Retrieve the most recent reasoning data for a session.

        Args:
            session_id: The session identifier

        Returns:
            Reasoning object with data if found, empty Reasoning object otherwise
        """
        return self.session_manager.get_reasoning(session_id)

    def get_reasoning_history(self, session_id: str) -> List[Reasoning]:
        """
        Retrieve all reasoning objects for a session.

        Args:
            session_id: The session identifier

        Returns:
            List of reasoning objects ordered by timestamp
        """
        return self.session_manager.get_reasoning_history(session_id)

    def add_tools(self, tools: List[Callable]):
        """
        Add tools to the agent

        Args:
            tools: List of tool functions decorated with @tool

        Returns:
            Self reference for chaining

        Raises:
            ValueError: If any function in tools is not decorated with @tool
            TypeError: If tools is not a list or contains non-callable items
            ValueError: If a tool with the same name already exists
        """
        self._validate_param(
            isinstance(tools, list),
            "tools must be a list of functions decorated with @tool",
            TypeError,
        )

        if not tools:
            return self  # Nothing to add

        tool_specs = []

        # Process each tool
        for i, tool in enumerate(tools):
            # Check if it's callable
            self._validate_param(
                callable(tool), f"Item at index {i} in tools is not callable", TypeError
            )

            # Ensure tool is decorated with @tool
            self._validate_param(
                hasattr(tool, "tool_spec"),
                f"Function '{tool.__name__}' must be decorated with @tool",
            )

            name = tool.tool_spec["name"]

            # Check for duplicate tool names
            self._validate_param(
                name not in self.tool_functions,
                f"A tool with name '{name}' already exists",
            )

            # Add tool function to mapping
            self.tool_functions[name] = tool

            # Create tool spec
            tool_specs.append(create_tool_spec(name, tool))

        # Add tool specs to existing configuration
        self.tool_config["tools"].extend(tool_specs)

        # Log tools added
        self.logger.info(
            f"Added {len(tools)} tools: {', '.join(t.tool_spec['name'] for t in tools)}"
        )

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

    def _validate_param(
        self, condition: bool, error_message: str, error_type=ValueError
    ) -> None:
        """
        Validate a condition and raise the specified error type with the provided message if it fails.

        Args:
            condition: The condition to check (should be True to pass validation)
            error_message: The error message to use if validation fails
            error_type: The type of error to raise (default: ValueError)

        Raises:
            Exception: If the condition is False, using the specified error_type
        """
        if not condition:
            raise error_type(error_message)

    def _get_aws_error_message(self, error: ClientError, service: str) -> str:
        """
        Get a user-friendly error message for AWS ClientErrors.

        Args:
            error: The ClientError exception
            service: The AWS service name (e.g., "Bedrock", "DynamoDB")

        Returns:
            A user-friendly error message
        """
        error_code = error.response.get("Error", {}).get("Code", "")

        error_messages = {
            "UnrecognizedClientException": f"Invalid AWS credentials. Please configure valid AWS credentials for Amazon {service} access.",
            "ExpiredTokenException": "AWS credentials have expired. Please refresh your AWS credentials.",
            "AccessDeniedException": f"Insufficient permissions to access Amazon {service}. Check your IAM permissions.",
            "AccessDenied": f"Insufficient permissions to access Amazon {service}. Check your IAM permissions.",
            "ServiceUnavailableException": f"Amazon {service} service is currently unavailable in this region.",
            "ValidationException": f"Invalid parameter provided to {service}: {str(error)}",
            "ResourceNotFoundException": f"The requested {service} resource was not found.",
        }

        return error_messages.get(
            error_code, f"{service} client error ({error_code}): {str(error)}"
        )

    def _get_general_error_message(
        self, error: Exception, service: str, region: str = None
    ) -> str:
        """
        Get a user-friendly error message for general exceptions.

        Args:
            error: The exception
            service: The AWS service name
            region: Optional AWS region

        Returns:
            A user-friendly error message
        """
        error_str = str(error)

        if "Could not connect to the endpoint URL" in error_str:
            return f"AWS credentials not found or invalid. Please configure AWS credentials for Amazon {service} access."
        elif "ExpiredToken" in error_str:
            return "AWS credentials have expired. Please refresh your AWS credentials."
        elif "not available in region" in error_str and region:
            return f"Amazon {service} is not available in region '{region}'. Choose a supported region."

        return f"Failed to initialize {service} client: {error_str}"

    def _update_realtime_reasoning(
        self, reasoning: Reasoning, session_id: str = None
    ) -> None:
        """
        Update reasoning data in real-time if conditions are met.

        Args:
            reasoning: The reasoning object to save
            session_id: Optional session identifier

        Returns:
            None
        """
        if session_id:
            self.session_manager.update_reasoning_if_needed(reasoning, session_id)

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
        self, tool_name: str, tool_inputs: Dict[str, Any], tool_use_id: str
    ) -> Dict[str, Any]:
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

            # Log successful tool execution
            self.logger.debug(f"Tool '{tool_name}' executed successfully")

            if self.display:
                self.display.show_tool_result(tool_name, result)

            # Format for API
            return {
                "toolUseId": tool_use_id,
                "content": [{"json": result}],
            }

        except Exception as err:
            # Handle errors
            error_message = str(err)

            # Always log tool errors
            self.logger.error(f"Tool '{tool_name}' failed: {error_message}")

            if self.display:
                self.display.show_tool_error(tool_name, error_message, tool_inputs)

            return {
                "toolUseId": tool_use_id,
                "content": [{"text": error_message}],
                "status": "error",
            }

    def run(
        self, input_text: str, session_id: Optional[str] = None
    ) -> Tuple[str, Reasoning]:
        """
        Process user input, invoke tools if necessary, and return the response with reasoning.
        Uses simple logging that creates a persistent log of each step.

        Args:
            input_text: The user's query/request
            session_id: Optional session identifier for persistent conversations.
                        Must contain only letters, numbers, underscores, and dashes,
                        and be 1-128 characters long.

        Returns:
            tuple: (agent_response, reasoning_object)
        """
        # Initialize messages - either from session or new conversation
        if self.session_manager.use_session_memory and session_id:
            # Validate session ID format
            if not self.session_manager.is_valid_session_id(session_id):
                error = "Invalid session_id format. Must contain only letters, numbers, underscores, dashes and be 1-128 characters."
                if self.display:
                    self.display.show_error(error)
                error_reasoning = Reasoning()
                error_reasoning.final_response = error
                return error, error_reasoning

            if self.session_manager.ddb_client:
                # Try to load existing session
                messages = self.session_manager.get_session_messages(session_id)
                if messages:
                    if self.display:
                        self.display.show_info(
                            f"Loaded existing session {session_id} with {len(messages)} messages"
                        )
                else:
                    # New session with this ID
                    messages = []
                    if self.display:
                        self.display.show_info(
                            f"Starting new session with ID: {session_id}"
                        )

                # Add the new user message
                messages.append({"role": "user", "content": [{"text": input_text}]})
            else:
                # DynamoDB client not initialized or failed
                messages = [{"role": "user", "content": [{"text": input_text}]}]
        else:
            # No session tracking, just start with the user message
            messages = [{"role": "user", "content": [{"text": input_text}]}]

        step_count = 0

        # Initialize reasoning object
        reasoning = Reasoning(session_id=session_id, query=input_text)

        # Log query at debug level
        self.logger.debug(f"Processing query: {input_text}")

        # Display reasoning if enabled
        if self.display:
            self.display.show_query(input_text)

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

                # Log step at debug level
                self.logger.debug(f"Processing step {step_count}")

                if self.display:
                    self.display.show_step_header(step_count)

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

                # Log thinking at debug level
                if thinking:
                    self.logger.debug(f"Agent rationale: {thinking}")

                    if self.display:
                        self.display.show_thinking(thinking)

                # Update reasoning with thinking
                if thinking:
                    reasoning = self.session_manager.update_reasoning(
                        reasoning=reasoning, thinking=thinking, step_number=step_count
                    )
                    self._update_realtime_reasoning(reasoning, session_id)

                    # Log the tools being called (debug level + display)
                    if tool_uses:
                        # Log tools at debug level
                        self.logger.debug(
                            f"Using {len(tool_names)} tools: {', '.join(tool_names)}"
                        )

                        if self.display:
                            self.display.show_tools(tool_uses)

                # Collect tool results for this step
                step_results = []

                if self.display:
                    self.display.show_tool_results_header()

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

                            # Add tool data to the reasoning object
                            if reasoning and reasoning.steps:
                                tool_data = ToolData(
                                    name=tool_name,
                                    inputs=tool_inputs,
                                    result=tool_result,
                                )
                                # Add to the tools list of the last step
                                reasoning.steps[-1].tools.append(tool_data)

                                # Update real-time reasoning after each tool use
                                self._update_realtime_reasoning(reasoning, session_id)

                # Send results back to model
                if step_results:
                    tool_result_message = {"role": "user", "content": step_results}
                    messages.append(tool_result_message)

                    if self.display:
                        self.display.show_step_delimiter()

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
                        self.logger.error(error_msg)
                        raise Exception(error_msg)
                else:
                    # No tool results
                    if self.display:
                        self.display.show_warning("No tool results were collected")
                    break

            # Check if we hit max steps
            if step_count == self.max_steps and response["stopReason"] == "tool_use":
                # Always log max steps warning
                self.logger.warning(
                    f"Maximum number of steps reached ({self.max_steps})"
                )

                if self.display:
                    self.display.show_max_steps_warning(self.max_steps)

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

                # Log final reasoning at debug level
                self.logger.debug(f"Final reasoning: {final_thinking}")

                if self.display:
                    self.display.show_final_reasoning(final_thinking)

                # Add final thinking to reasoning object
                reasoning.final_thinking = final_thinking

                clean_response = final_output.split("</thinking>")[-1].strip()
            else:
                clean_response = final_output.strip()

            # Add final response to reasoning object
            reasoning.final_response = clean_response

            # Log completion at debug level
            self.logger.debug(f"Query completed with {step_count} steps")

            if self.display:
                # Display completion status
                self.display.show_completion(step_count)

                # Display final response
                self.display.show_final_response(clean_response)

            # Save final conversation and reasoning to DynamoDB if using session memory
            if (
                self.session_manager.use_session_memory
                and session_id
                and self.session_manager.ddb_client
            ):
                # Note: The final assistant message has already been added to messages
                # in the main processing loop (line ~471), so we don't need to add it again

                # Save messages to DynamoDB
                self.session_manager.save_session_messages(session_id, messages)
                # Save final reasoning data
                self.session_manager.save_reasoning_data(session_id, reasoning)
                if self.display:
                    self.display.show_info(
                        f"Saved conversation history and reasoning for session {session_id}"
                    )

            return clean_response, reasoning

        except Exception as e:
            error_message = f"Error while processing request: {str(e)}"

            # Always log the error
            self.logger.error(f"Error processing request: {error_message}")

            # Display the error if reasoning display is enabled
            if self.display:
                self.display.show_error(error_message)

            error_reasoning = Reasoning()
            error_reasoning.final_response = error_message
            return error_message, error_reasoning
