# Getting Started with MinimalAgent

This guide will help you quickly build an agentic application using MinimalAgent and Amazon Bedrock.

MinimalAgent is essentially a wrapper over the Bedrock Covnerse API (with optional session management using DDB), making it a simple framework for quickly bootstrapping AWS-native agents. It currently lacks integration with observability tools like Langfuse, so for large-scale production deployments I encourage you to use another framework.

## Installation

```bash
pip install minimalagent
```

!!! tip
Make sure you have Python 3.8 or newer installed.

## 1. Create Your First Agent

Let's create a simple agent that can retrieve weather information:

```python
from minimalagent import Agent, tool

# Define a tool
@tool
def get_weather(location: str) -> dict:
    """Get current weather conditions.

    Args:
        location: City name to get weather for

    Returns:
        Weather information dictionary
    """
    # In a real app, you would call a weather API
    return {
        "temperature": 72,
        "condition": "sunny",
        "humidity": "45%",
        "location": location
    }

# Create and run the agent
agent = Agent(tools=[get_weather])
response, reasoning = agent.run("What's the weather in Tokyo?")

print(response)
```

## 2. Add Multiple Tools

Agents become more powerful when they have multiple tools available:

```python
@tool
def search_wiki(query: str, max_results: int = 3) -> list:
    """Search Wikipedia for information.

    Args:
        query: Search terms
        max_results: Maximum number of results to return

    Returns:
        List of search results
    """
    # Simulate search results
    return [
        {"title": f"Result for {query}", "snippet": f"Information about {query}..."},
        {"title": f"Another result for {query}", "snippet": "More information..."}
    ][:max_results]

@tool
def calculate(expression: str) -> dict:
    """Calculate a mathematical expression.

    Args:
        expression: The math expression to evaluate

    Returns:
        Result of the calculation
    """
    try:
        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e), "expression": expression}

# Create agent with multiple tools
agent = Agent(
    tools=[get_weather, search_wiki, calculate],
    show_reasoning=True  # Show reasoning process in the terminal
)
```

## 3. Enable Session Memory

Add memory to your agent so it can remember previous interactions:

```python
# Create agent with session support
agent = Agent(
    tools=[get_weather, search_wiki, calculate],
    use_session_memory=True  # Enable persistent memory
)

# First interaction
response1, _ = agent.run(
    "What's the weather in Seattle?",
    session_id="user123"  # Unique identifier for this conversation
)

# Follow-up question (agent will remember previous context)
response2, _ = agent.run(
    "How about in Portland?",
    session_id="user123"  # Same session ID connects the conversations
)
```

## 4. Customize Agent Behavior

Adjust the agent's capabilities and behavior:

```python
agent = Agent(
    # Tool configuration
    tools=[get_weather, search_wiki],
    max_steps=10,  # Allow more tool use iterations for complex tasks

    # Display configuration
    show_reasoning=True,  # Show colorized reasoning in terminal
    log_level="INFO",  # More detailed logging (DEBUG, INFO, WARNING, ERROR)

    # Model configuration
    model_id="us.amazon.nova-pro-v1:0",  # Specify Bedrock model
    system_prompt="You are a helpful weather assistant that provides accurate forecasts.",

    # Session configuration
    use_session_memory=True,
    session_ttl=7200,  # 2-hour session timeout
)
```

## 5. Access Reasoning Information

See how the agent thinks and uses tools:

```python
response, reasoning = agent.run("What's the temperature in Paris and London?")

# Display reasoning process
print(f"Query: {reasoning.query}")
print(f"Steps: {reasoning.total_steps}")

for step in reasoning.steps:
    print(f"\nStep {step.step_number} thinking:")
    print(step.thinking)

    for tool in step.tools:
        print(f"Tool: {tool.name}")
        print(f"Inputs: {tool.inputs}")
        print(f"Result: {tool.result}")

print(f"\nFinal response: {reasoning.final_response}")
```

## 6. Put It All Together

Here's a complete example showing the main features:

```python
from minimalagent import Agent, tool

@tool
def get_weather(location: str) -> dict:
    """Get weather information for a location."""
    # Simulate weather data
    return {"temperature": 75, "condition": "sunny", "location": location}

@tool
def convert_temperature(celsius: float) -> dict:
    """Convert Celsius to Fahrenheit."""
    fahrenheit = (celsius * 9/5) + 32
    return {"celsius": celsius, "fahrenheit": fahrenheit}

# Create agent
agent = Agent(
    tools=[get_weather, convert_temperature],
    use_session_memory=True,
    show_reasoning=True,
    system_prompt="You are a helpful weather assistant."
)

# Run queries in a session
session_id = "weather-session-1"

# First query
response1, reasoning1 = agent.run(
    "What's the weather in Paris?",
    session_id=session_id
)
print(f"Response: {response1}")

# Follow-up query
response2, reasoning2 = agent.run(
    "Convert that temperature to Fahrenheit.",
    session_id=session_id
)
print(f"Response: {response2}")

# Get reasoning history to see all interactions
history = agent.get_reasoning_history(session_id)
print(f"Session has {len(history)} interactions")
```

## AWS Credentials

MinimalAgent uses Amazon Bedrock, so you'll need to set up AWS credentials:

1. Configure credentials using the AWS CLI: `aws configure`
2. Or set environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-west-2
```

!!! warning "Permissions Required"
Ensure your AWS credentials have permissions to access the Amazon Bedrock service.

## Next Steps

- Explore the [Tool Creation Guide](guide/tools.md) to build more powerful tools
- Learn about [Session Management](guide/sessions.md) for persistent conversations
- Customize the [Reasoning Display](guide/logging.md) for better visibility
- Understand [Reasoning Data](guide/models.md) for analyzing agent behavior
- Check out the [API Reference](api/agent.md) for detailed documentation
