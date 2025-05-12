# Configuration Options

MinimalAgent provides numerous configuration options to tailor the agent's behavior to your specific needs. This comprehensive guide covers all available configuration settings.

## Agent Configuration

When creating an agent, you can provide various configuration parameters:

```python
from minimalagent import Agent

agent = Agent(
    # Tool configuration
    tools=[tool1, tool2],                  # List of tools available to the agent
    max_steps=5,                          # Maximum number of tool invocation steps
    
    # Model configuration
    model_id="us.amazon.nova-pro-v1:0",   # Amazon Bedrock model ID
    bedrock_region="us-west-2",           # AWS region for Bedrock
    system_prompt="You are a helpful...",  # Custom system prompt
    
    # Display and logging
    show_reasoning=True,                  # Display reasoning in terminal
    log_level="INFO",                     # Logging verbosity
    
    # Session configuration
    use_session_memory=True,              # Enable session persistence
    session_table_name="my-agent-table",  # DynamoDB table name
    memory_region="us-east-1",            # AWS region for DynamoDB
    session_ttl=3600,                     # Session TTL in seconds (1 hour)
    real_time_reasoning=True,             # Enable real-time reasoning updates
)
```

## Complete Parameter Reference

This table provides detailed information about all available parameters, their defaults, validation rules, and descriptions:

| Parameter | Type | Default | Validation | Description |
|-----------|------|---------|-----------|-------------|
| **Tool Configuration** |
| `tools` | `List[Callable]` | `None` | Must be decorated with `@tool` | List of tool functions available to the agent |
| `max_steps` | `int` | `5` | Must be > 0 | Maximum number of tool use iterations |
| **Model Configuration** |
| `model_id` | `str` | `"us.amazon.nova-pro-v1:0"` | Must be a valid Bedrock model | Amazon Bedrock model ID |
| `bedrock_region` | `str` | `"us-west-2"` | Valid AWS region | AWS region for Bedrock |
| `system_prompt` | `str` | `""` | None | Custom instructions for the model |
| **Display and Logging** |
| `show_reasoning` | `bool` | `True` | None | Show colorized reasoning in terminal |
| `log_level` | `str` | `"WARNING"` | Must be one of: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" | Controls logging verbosity |
| **Session Configuration** |
| `use_session_memory` | `bool` | `False` | None | Enable persistent sessions with DynamoDB |
| `session_table_name` | `str` | `"minimalagent-session-table"` | 3-255 chars, alphanumeric plus hyphens, dots, underscores | DynamoDB table name |
| `memory_region` | `str` | Same as `bedrock_region` | Valid AWS region | AWS region for DynamoDB |
| `session_ttl` | `int` | `3600` (1 hour) | Must be > 0 | Session expiration in seconds |
| `real_time_reasoning` | `bool` | `False` | Requires `use_session_memory=True` | Update reasoning during execution |

### Parameter Interactions and Dependencies

Some parameters have special behaviors or dependencies:

- **`memory_region`**: If not specified, defaults to the same value as `bedrock_region`
- **`real_time_reasoning`**: Only works when `use_session_memory=True`
- **`session_table_name`**: If a custom name is provided, `use_session_memory` is automatically enabled
- **`show_reasoning`**: Controls visual display only; reasoning data is always returned by the `run()` method

### Parameter Validation

MinimalAgent validates all parameters at initialization:

```python
# This will raise an error
agent = Agent(
    max_steps=-1,  # Error: max_steps must be greater than 0
    log_level="VERBOSE",  # Error: invalid log level
    session_ttl=0  # Error: session_ttl must be greater than 0
)
```

If any validation fails, a `ValueError` will be raised with a descriptive error message.

## AWS Configuration

### Credentials and Regions

MinimalAgent uses boto3 for AWS interactions. Configure credentials:

```python
# Using environment variables (recommended)
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
import os
os.environ["AWS_ACCESS_KEY_ID"] = "YOUR_ACCESS_KEY"
os.environ["AWS_SECRET_ACCESS_KEY"] = "YOUR_SECRET_KEY"
os.environ["AWS_REGION"] = "us-west-2"

# Using AWS CLI configuration
# Run 'aws configure' before starting your application
```

## Configuration Precedence

When multiple configuration methods are used, MinimalAgent follows this precedence (highest to lowest):

1. Environment variables
2. Default AWS credential discovery
3. Default parameter values

## System Prompt Configuration

The system prompt controls the agent's behavior and personality:

```python
# Expert mode system prompt
expert_prompt = """
You are an expert data scientist with extensive knowledge of statistical analysis and machine learning.
Always provide detailed, technical explanations with references to relevant statistical methods or algorithms.
"""

agent = Agent(
    tools=[...],
    system_prompt=expert_prompt
)
```

!!! tip
    Keep system prompts concise and specific to avoid overwhelming the model with instructions.

## Dynamic Configuration

Some parameters can be reconfigured after agent creation:

```python
# Create agent with initial configuration
agent = Agent(tools=[tool1, tool2])

# Add more tools later
agent.add_tools([tool3, tool4])

# Update max steps
agent.max_steps = 15
```

## Environment Variables

MinimalAgent respects these environment variables:

```bash
# AWS Credentials
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="us-west-2"
```

## Complete Configuration Example

```python
from minimalagent import Agent, tool
import logging

# Setup custom logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="agent.log"
)
logger = logging.getLogger("agent_logger")

# Define a tool
@tool
def search(query: str) -> dict:
    """Search for information."""
    return {"results": [f"Result for {query}"]}

# Create agent with comprehensive configuration
agent = Agent(
    # Tool configuration
    tools=[search],
    system_prompt="You are a helpful search assistant.",
    max_steps=8,
    
    # Model configuration
    model_id="us.amazon.nova-pro-v1:0",
    bedrock_region="us-west-2",
    
    # Display and logging
    show_reasoning=True,
    log_level="INFO",
    
    # Session configuration
    use_session_memory=True,
    session_table_name="search-agent-sessions",
    memory_region="us-west-2",
    session_ttl=3600,  # 1 hour
    real_time_reasoning=True,
)

# Run a query
response, reasoning = agent.run(
    "Find information about machine learning",
    session_id="user-session-123"
)
```

## Configuration Best Practices

1. **Start Simple**: Begin with minimal configuration and add options as needed
2. **Match Resources**: Adjust `max_steps` based on task complexity
3. **Secure Credentials**: Use environment variables rather than hardcoded credentials
4. **Test Thoroughly**: Create a testing environment with local DynamoDB before production
5. **Monitor Usage**: Watch your AWS usage, especially with real-time reasoning enabled
6. **Optimize TTL**: Set session TTL appropriate for your application's conversation patterns