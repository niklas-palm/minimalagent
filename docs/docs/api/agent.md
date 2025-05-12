# Agent API Reference

The Agent class is the central component of MinimalAgent that processes inputs, invokes tools, and manages sessions.

## Agent Class

::: minimalagent.agent.Agent
    options:
      show_root_heading: true
      show_source: false

## Usage Examples

### Basic Initialization

```python
from minimalagent import Agent, tool

# Define a sample tool
@tool
def hello(name: str) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}

# Initialize the agent with default settings
agent = Agent(tools=[hello])

# Run a query
response, reasoning = agent.run("Say hello to Alice")
print(response)  # Output: Hello, Alice!
```

### Customized Agent

```python
from minimalagent import Agent

# Initialize with customized parameters
agent = Agent(
    tools=[],  # No tools initially
    max_steps=10,  # Allow up to 10 tool invocation steps
    show_reasoning=True,  # Display colorized reasoning
    log_level="INFO",  # Set logging verbosity
    model_id="us.amazon.claude-3-haiku-20240307-v1:0",  # Use Claude 3 Haiku
    bedrock_region="us-east-1",  # Set AWS region
    system_prompt="You are a helpful assistant specializing in weather information.",
)

# Add tools later
agent.add_tools([get_weather, get_forecast])

# Enable session memory
agent.session_manager.use_session_memory = True
```

### Session Management

```python
# Create an agent with session memory
agent = Agent(
    tools=[some_tool],
    use_session_memory=True,
    session_table_name="my-custom-table",  # Custom DynamoDB table name
    real_time_reasoning=True,  # Update reasoning during execution
)

# Run with a session ID to enable persistence
response, reasoning = agent.run("What's the weather?", session_id="user123")

# Get reasoning data from a previous session
previous_reasoning = agent.get_reasoning("user123")
print(f"Previous query: {previous_reasoning.query}")
print(f"Steps taken: {previous_reasoning.total_steps}")

# Get full history for a session
history = agent.get_reasoning_history("user123")
for item in history:
    print(f"Query: {item.query}")
    print(f"Response: {item.final_response}")
```