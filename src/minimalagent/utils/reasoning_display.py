"""Display utilities for agent reasoning."""

import json
from typing import Any, Dict, List


class ReasoningDisplay:
    """
    Handles displaying reasoning steps, tool executions, and other information
    during agent execution. Encapsulates all formatting and display logic.
    """

    def __init__(self, logger):
        """
        Initialize the reasoning display.

        Args:
            logger: Logger with display_* methods
        """
        self.logger = logger

    def show_query(self, query: str) -> None:
        """
        Display the initial query.

        Args:
            query: The user's query text
        """
        self.logger.display_print("")
        self.logger.display_query(f"QUERY: {query}")
        self.logger.display_print("")
        self.logger.display_delimiter()

    def show_step_header(self, step_number: int) -> None:
        """
        Display a step header.

        Args:
            step_number: The current step number
        """
        self.logger.display_print("")
        self.logger.display_step(f"STEP {step_number}")
        self.logger.display_subdelimiter()

    def show_thinking(self, thinking: str) -> None:
        """
        Display the agent's thinking/rationale.

        Args:
            thinking: The thinking text
        """
        self.logger.display_print("")
        self.logger.display_step("RATIONALE:")
        self.logger.display_thinking(thinking)
        self.logger.display_print("")

    def show_tools(self, tools: List[Dict[str, Any]]) -> None:
        """
        Display the tools being used.

        Args:
            tools: List of tool use objects
        """
        tool_names = [t["name"] for t in tools]

        self.logger.display_step(f"ACTIONS ({len(tool_names)} tools):")

        for i, tool in enumerate(tools, 1):
            tool_name = tool["name"]
            tool_inputs = json.dumps(tool["input"], indent=2) if tool["input"] else "{}"
            self.logger.display_print(f"{i}. {tool_name}({tool_inputs})")

        self.logger.display_print("")

    def show_tool_results_header(self) -> None:
        """Display the header for tool results."""
        self.logger.display_tool("## TOOL RESULTS")
        self.logger.display_print("")

    def show_tool_result(self, tool_name: str, result: Any) -> None:
        """
        Display an individual tool result.

        Args:
            tool_name: The name of the tool
            result: The tool result
        """
        self.logger.display_action(f"✓ {tool_name}:")
        self.logger.display_print(json.dumps(result, indent=2))
        self.logger.display_print("")

    def show_tool_error(
        self, tool_name: str, error_message: str, inputs: Dict[str, Any]
    ) -> None:
        """
        Display a tool error.

        Args:
            tool_name: The name of the tool
            error_message: The error message
            inputs: The tool inputs
        """
        self.logger.display_error(f"✗ {tool_name} ERROR:")
        self.logger.display_error(f"Error: {error_message}")
        self.logger.display_print(f"Inputs: {json.dumps(inputs, indent=2)}")
        self.logger.display_print("")

    def show_step_delimiter(self) -> None:
        """Display a delimiter between steps."""
        self.logger.display_subdelimiter()

    def show_max_steps_warning(self, max_steps: int) -> None:
        """
        Display a warning when max steps is reached.

        Args:
            max_steps: The maximum number of steps
        """
        self.logger.display_print("")
        self.logger.display_error(f"! Maximum number of steps reached ({max_steps})")
        self.logger.display_print("")

    def show_final_reasoning(self, final_thinking: str) -> None:
        """
        Display the final reasoning.

        Args:
            final_thinking: The final thinking text
        """
        self.logger.display_print("")
        self.logger.display_step("FINAL REASONING:")
        self.logger.display_subdelimiter()
        self.logger.display_thinking(final_thinking)
        self.logger.display_print("")

    def show_completion(self, step_count: int) -> None:
        """
        Display completion status.

        Args:
            step_count: The number of steps completed
        """
        self.logger.display_print("")
        self.logger.display_delimiter()
        self.logger.display_final(f"COMPLETE - {step_count} steps")
        self.logger.display_print("")

    def show_final_response(self, response: str) -> None:
        """
        Display the final response.

        Args:
            response: The agent's final response
        """
        self.logger.display_print("")
        self.logger.display_final("FINAL RESPONSE:")
        self.logger.display_subdelimiter()
        print(response)
        self.logger.display_subdelimiter()

    def show_error(self, error_message: str) -> None:
        """
        Display an error message.

        Args:
            error_message: The error message
        """
        self.logger.display_print("")
        self.logger.display_error("ERROR:")
        self.logger.display_subdelimiter()
        print(error_message)
        self.logger.display_subdelimiter()

    def show_info(self, message: str) -> None:
        """
        Display an informational message.

        Args:
            message: The message to display
        """
        self.logger.display_print("")
        self.logger.display_info(f"INFO: {message}")
        self.logger.display_print("")

    def show_warning(self, message: str) -> None:
        """
        Display a warning message.

        Args:
            message: The warning message to display
        """
        self.logger.display_print("")
        self.logger.display_step("WARNING:")
        self.logger.display_print(message)
        self.logger.display_print("")
