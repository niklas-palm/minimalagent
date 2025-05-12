# Getting Started

This guide will help you get up and running with MinimalAgent in minutes.

## Installation

Install MinimalAgent using pip:

```bash
pip install minimalagent
```

!!! tip
    Make sure you have Python 3.8 or newer installed.

## Basic Usage

Create a simple agent with a custom tool:

```python
from minimalagent import Agent, tool

# Define a tool
@tool
def get_weather(location: str, units: str = "metric") -> dict:
    """Get weather information for a location.
    
    Args:
        location: City name or location
        units: Units to use (metric or imperial)
        
    Returns:
        Weather data dictionary
    """
    # In a real application, you would call a weather API
    return {
        "location": location,
        "temperature": 22,
        "conditions": "sunny",
        "units": units
    }

# Create an agent with the tool
agent = Agent(
    tools=[get_weather],
    show_reasoning=True,  # Show colorized reasoning in terminal
    log_level="INFO",     # Set logging level
)

# Send a query to the agent
response, reasoning = agent.run("What's the weather in Seattle?")

# Print the response
print(f"\nFinal response: {response}")

# Print details about the reasoning process
print(f"Steps taken: {reasoning.total_steps}")
print(f"Query: {reasoning.query}")
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

Now that you have MinimalAgent up and running, you can:

- Learn more about [Tool Creation](guide/tools.md)
- Explore [Session Management](guide/sessions.md) for persistent conversations
- Customize the [Reasoning Display](guide/logging.md) for better visibility
- Check out the [Examples](examples/basic.md) for more advanced usage