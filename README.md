# MinimalAgent

A lightweight agent framework for building agentic applications with Amazon Bedrock.

## Installation

```bash
pip install minimalagent
```

## Quick Start

```python
from minimalagent import Agent, tool

@tool
def get_weather(location: str):
    """Get weather for a location.

    Args:
        location: City name to get weather for

    Returns:
        Weather data dictionary
    """
    # Your implementation here
    return {"temperature": 22, "condition": "sunny"}

# Create agent
agent = Agent(tools=[get_weather])

# Run a query
response, reasoning = agent.run("What's the weather in San Francisco?")
print(response)
```

## Key Features

- **Simple API**: Intuitive design with minimal boilerplate
- **Tool-first approach**: Easy tool creation with docstring parsing
- **Built-in session memory**: Persistent conversations via DynamoDB
- **Step-by-step reasoning**: Visibility into the agent's thought process

MinimalAgent is essentially a wrapper over the Bedrock Covnerse API (with optional session management using DDB), making it a simple framework for quickly bootstrapping AWS-native agents. It currently lacks integration with observability tools like Langfuse, so for large-scale production deployments I encourage you to use another framework.

## Core Concepts

### Tools

Tools give your agent capabilities. Simply decorate functions with `@tool`:

```python
@tool
def search_database(query: str, limit: int = 10) -> list:
    """Search the database for records matching the query."""
    # Your implementation here
    return [{"id": 1, "name": query}]
```

### Session Management

Enable persistent conversations across multiple interactions:

```python
# Create an agent with session support
agent = Agent(use_session_memory=True)

# Use a consistent session ID for the same conversation
response1 = agent.run("Find information about electric cars", session_id="user123")
response2 = agent.run("What about hybrid models?", session_id="user123")  # Remembers context
```

### Reasoning Display

Control the visibility of the agent's thinking process:

```python
# Colorized reasoning in the terminal is enabled by default
agent = Agent(tools=[get_weather])  # show_reasoning=True is the default

# Explicitly enable reasoning display
agent_with_display = Agent(
    tools=[get_weather],
    show_reasoning=True
)

# Hide reasoning output for production use
agent_without_display = Agent(
    tools=[get_weather],
    show_reasoning=False,
    log_level="WARNING"  # Only log warnings and errors
)
```

### Reasoning Process

Access the agent's step-by-step thinking programmatically:

```python
response, reasoning = agent.run("Calculate 25 * 4 + 10")

# Access reasoning data
print(f"Query: {reasoning.query}")
print(f"Steps: {reasoning.total_steps}")
for step in reasoning.steps:
    print(f"Step {step.step_number} thinking: {step.thinking}")
```

## Documentation

For more detailed documentation, visit [https://niklas-palm.github.io/minimalagent/](https://niklas-palm.github.io/minimalagent/)

## AWS Setup

MinimalAgent requires AWS credentials for accessing Amazon Bedrock and DynamoDB.

### Option 1: AWS CLI Configuration (Recommended)

1. Install and configure the AWS CLI:
   ```bash
   aws configure
   ```

### Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_REGION=us-west-2
```

## License

MIT
