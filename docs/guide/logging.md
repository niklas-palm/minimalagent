# Reasoning Display and Logging

MinimalAgent provides visibility into the agent's thinking process through both visual output and programmatic access to reasoning data.

## Visual Reasoning Display

The agent can display its reasoning process directly in the terminal:

```python
from minimalagent import Agent, tool

@tool
def search(query: str) -> dict:
    """Search for information."""
    return {"results": f"Results for {query}"}

# By default, colorized reasoning is shown in the terminal
agent = Agent(tools=[search])
response, reasoning = agent.run("Find information about machine learning")
```

The display includes:
- The original query
- Each thinking step
- Tools being used with their inputs
- Tool results
- The final response

This makes it easy to understand how the agent reached its conclusion and which tools it used.

## Controlling the Display

You can enable or disable the colorized reasoning display:

```python
# Enable reasoning display (default)
agent = Agent(
    tools=[search],
    show_reasoning=True
)

# Disable reasoning display for production
agent = Agent(
    tools=[search],
    show_reasoning=False
)
```

## Accessing Reasoning Data Programmatically

Even when visual display is disabled, you can access the complete reasoning data:

```python
# Disable visual display but still capture reasoning data
agent = Agent(tools=[search], show_reasoning=False)
response, reasoning = agent.run("Search for quantum computing")

# Access reasoning data programmatically
print(f"Query: {reasoning.query}")
print(f"Steps taken: {reasoning.total_steps}")

# Examine each step
for step in reasoning.steps:
    print(f"Step {step.step_number} thinking: {step.thinking}")
    
    # Examine tools used
    for tool in step.tools:
        print(f"Tool: {tool.name}")
        print(f"Inputs: {tool.inputs}")
        print(f"Result: {tool.result}")
```

This allows you to build your own visualizations or analytics on top of the reasoning data.

## Agent Log Levels

The agent's log level controls what information is logged during operation:

```python
# Minimal logging (warnings and errors only)
agent = Agent(
    tools=[search],
    log_level="WARNING"  # Default
)

# Informational logs (good for general use)
agent = Agent(
    tools=[search],
    log_level="INFO"
)

# Verbose debugging (most detailed)
agent = Agent(
    tools=[search],
    log_level="DEBUG"
)
```

Available log levels from least to most verbose:
- `"CRITICAL"` - Only critical errors
- `"ERROR"` - Error messages
- `"WARNING"` - Warnings and errors (default)
- `"INFO"` - General information plus warnings and errors
- `"DEBUG"` - Detailed debug information plus everything above

## Common Logging Scenarios

### Development/Debugging

For maximum visibility during development:

```python
agent = Agent(
    tools=[search],
    show_reasoning=True,  # See colorized reasoning
    log_level="DEBUG"     # Maximum logging detail
)
```

### Production

For production environments:

```python
agent = Agent(
    tools=[search],
    show_reasoning=False,  # No visual display
    log_level="WARNING"    # Only important warnings and errors
)
```

### Monitoring

For monitoring in production while maintaining some visibility:

```python
agent = Agent(
    tools=[search],
    show_reasoning=False,  # No visual display
    log_level="INFO"       # Information about operations, warnings, and errors
)
```

## Advanced: Integration with Python Logging

MinimalAgent integrates with Python's standard logging system, allowing you to capture logs in your application's logging infrastructure:

```python
import logging

# Configure Python's logging system
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="agent.log"  # Save to a file instead of console
)

# MinimalAgent will use this logging configuration
agent = Agent(
    tools=[search],
    log_level="INFO",  # This level applies to MinimalAgent's logger
)
```

This is useful for:
- Saving logs to files instead of the console
- Integrating with existing logging infrastructure
- Custom log formatting
- Log rotation and management