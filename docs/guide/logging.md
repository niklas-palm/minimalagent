# Reasoning Display and Logging

MinimalAgent provides rich, colorful display of agent reasoning along with comprehensive logging options. This guide shows you how to customize the display and logging to better understand your agent's behavior.

## Enabling the Reasoning Display

The reasoning display shows the agent's thinking steps, tool usage, and final response in a colorful, structured format:

```python
from minimalagent import Agent

agent = Agent(
    tools=[...],
    show_reasoning=True,  # Enable colorized reasoning display
)

# The reasoning will be displayed in the console when run() is called
response, reasoning = agent.run("What's the weather in Seattle?")
```

!!! tip
    The reasoning display is particularly useful during development to understand how the agent processes queries.

## Customizing Display Colors

You can customize the colors used in the reasoning display:

```python
from minimalagent import Agent
from minimalagent.utils.reasoning_display import DisplayConfig

# Create custom color scheme
custom_colors = DisplayConfig(
    thinking_color="cyan",
    tool_name_color="magenta",
    tool_input_color="yellow",
    tool_result_color="green",
    final_thinking_color="blue",
    final_response_color="white",
)

# Use custom colors in the agent
agent = Agent(
    tools=[...],
    show_reasoning=True,
    display_config=custom_colors,
)
```

Available colors include: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`, and their bright variants (e.g., `bright_red`).

## Display Formatting Options

Control the display format with these options:

```python
from minimalagent import Agent

agent = Agent(
    tools=[...],
    show_reasoning=True,
    display_step_numbers=True,  # Show step numbers (default: True)
    display_timestamps=True,    # Show timestamps for each step (default: False)
    display_thinking=True,      # Show agent thinking (default: True)
    tool_result_max_length=100, # Truncate long tool results (default: 500)
)
```

## Logging Configuration

MinimalAgent integrates with Python's built-in logging system. Configure the log level:

```python
from minimalagent import Agent

agent = Agent(
    tools=[...],
    log_level="INFO",  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
)
```

Log levels control what information is output:
- `DEBUG`: All details including tool executions and API calls
- `INFO`: Important information plus warnings and errors
- `WARNING`: Warning and error messages only
- `ERROR`: Only error messages
- `CRITICAL`: Only critical errors

## Custom Logger Configuration

You can customize the logger for more advanced logging:

```python
import logging
from minimalagent import Agent
from minimalagent.utils.logging import setup_logger

# Configure a custom logger
custom_logger = logging.getLogger("my_custom_logger")
custom_logger.setLevel(logging.INFO)

# Add a file handler
file_handler = logging.FileHandler("agent.log")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
custom_logger.addHandler(file_handler)

# Use the custom logger with the agent
agent = Agent(
    tools=[...],
    logger=custom_logger,
)
```

## Separating Reasoning Display from Logging

You can enable logging without the colorized display:

```python
from minimalagent import Agent

agent = Agent(
    tools=[...],
    show_reasoning=False,  # Disable colorized display
    log_level="INFO",      # Still log important information
)
```

## Capturing Reasoning Data

Even when not displaying reasoning, you can still capture and analyze it:

```python
from minimalagent import Agent

agent = Agent(
    tools=[...],
    show_reasoning=False,  # No visual display
)

response, reasoning = agent.run("What's the weather in Seattle?")

# Extract information from reasoning
print(f"Query: {reasoning.query}")
print(f"Steps: {reasoning.total_steps}")

# Analyze individual steps
for i, step in enumerate(reasoning.steps):
    print(f"Step {i+1} thinking: {step.thinking}")
    
    # Check tools used
    for tool in step.tools:
        print(f"Tool used: {tool.name}")
        print(f"Inputs: {tool.inputs}")
        print(f"Result: {tool.result}")
```

## Logging in Production

For production environments, consider these best practices:

```python
import logging
from minimalagent import Agent

# Configure production logging
logging.basicConfig(
    filename="agent_production.log",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.WARNING,  # Higher threshold for production
)

# Create agent with minimal console output
agent = Agent(
    tools=[...],
    show_reasoning=False,  # Disable console display
    log_level="WARNING",   # Log only warnings and errors
)
```

## Debugging with Enhanced Logging

For debugging difficult issues, use enhanced logging:

```python
from minimalagent import Agent

# Enable detailed debugging
agent = Agent(
    tools=[...],
    show_reasoning=True,
    log_level="DEBUG",      # Most verbose logging
    display_timestamps=True,
    display_step_numbers=True,
)

# The run will show maximum detail
response, reasoning = agent.run("What's the weather in Seattle?")
```

## Complete Example

```python
from minimalagent import Agent, tool
from minimalagent.utils.reasoning_display import DisplayConfig
import logging

# Create a tool
@tool
def multiply(a: float, b: float) -> dict:
    """Multiply two numbers."""
    return {"result": a * b}

# Setup custom logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Custom display colors
display_config = DisplayConfig(
    thinking_color="bright_cyan",
    tool_name_color="bright_green",
    tool_input_color="bright_yellow",
    tool_result_color="bright_magenta",
    final_thinking_color="bright_blue",
    final_response_color="bright_white",
)

# Create the agent
agent = Agent(
    tools=[multiply],
    show_reasoning=True,
    log_level="INFO",
    display_config=display_config,
    display_timestamps=True,
)

# Run a query
response, reasoning = agent.run("What is 12 times 34?")
```