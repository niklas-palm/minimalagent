# Configuration Options

MinimalAgent provides numerous configuration options to tailor the agent's behavior to your specific needs. This comprehensive guide covers all available configuration settings.

## Agent Configuration

When creating an agent, you can provide various configuration parameters:

```python
from minimalagent import Agent

agent = Agent(
    # Basic configuration
    tools=[tool1, tool2],                  # List of tools available to the agent
    system_prompt="You are a helpful...",  # Custom system prompt
    max_steps=5,                          # Maximum number of tool invocation steps
    
    # Model configuration
    model_id="us.amazon.nova-pro-v1:0",   # Amazon Bedrock model ID
    bedrock_region="us-west-2",           # AWS region for Bedrock
    temperature=0.7,                      # Response temperature (0.0 to 1.0)
    top_p=0.9,                            # Top-p sampling parameter
    
    # Display and logging
    show_reasoning=True,                  # Display reasoning in terminal
    log_level="INFO",                     # Logging verbosity
    
    # Session configuration
    use_session_memory=True,              # Enable session persistence
    session_table_name="my-agent-table",  # DynamoDB table name
    memory_region="us-east-1",            # AWS region for DynamoDB
    session_ttl=86400,                    # Session TTL in seconds (24 hours)
    real_time_reasoning=True,             # Enable real-time reasoning updates
    
    # Advanced options
    max_reasoning_size=102400,            # Maximum reasoning size in bytes
    dynamodb_endpoint_url=None,           # Custom DynamoDB endpoint
    aws_profile=None,                     # AWS profile name
)
```

## Core Configuration Parameters

### Tools and Behavior

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `list` | `[]` | List of tool functions available to the agent |
| `system_prompt` | `str` | *Default prompt* | Instructions for the agent |
| `max_steps` | `int` | `10` | Maximum number of tool invocation steps |

### Model Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model_id` | `str` | `"us.amazon.nova-pro-v1:0"` | Amazon Bedrock model ID |
| `bedrock_region` | `str` | `"us-west-2"` | AWS region for Bedrock |
| `temperature` | `float` | `0.7` | Response temperature (0.0-1.0) |
| `top_p` | `float` | `0.9` | Top-p sampling parameter |
| `max_tokens` | `int` | `4096` | Maximum tokens in model response |

### Display and Logging

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_reasoning` | `bool` | `False` | Show colorized reasoning in terminal |
| `log_level` | `str` | `"WARNING"` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `logger` | `logging.Logger` | `None` | Custom logger instance |
| `display_config` | `DisplayConfig` | *Default colors* | Custom display color configuration |
| `display_step_numbers` | `bool` | `True` | Show step numbers in display |
| `display_timestamps` | `bool` | `False` | Show timestamps in display |
| `display_thinking` | `bool` | `True` | Show agent thinking in display |
| `tool_result_max_length` | `int` | `500` | Maximum length for displayed tool results |

### Session Management

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_session_memory` | `bool` | `False` | Enable session persistence |
| `session_table_name` | `str` | `"minimalagent-sessions"` | DynamoDB table name |
| `memory_region` | `str` | `None` | AWS region for DynamoDB (defaults to bedrock_region if not specified) |
| `session_ttl` | `int` | `86400` | Session TTL in seconds (24 hours) |
| `real_time_reasoning` | `bool` | `False` | Enable real-time reasoning updates |
| `max_reasoning_size` | `int` | `51200` | Maximum reasoning size in bytes (50 KB) |

## AWS Configuration

### Credentials and Regions

MinimalAgent uses boto3 for AWS interactions. Configure credentials:

```python
# Explicit AWS profile
agent = Agent(
    tools=[...],
    aws_profile="my-profile",  # Use a specific profile from ~/.aws/credentials
)

# Explicit credentials (not recommended - use environment variables instead)
import boto3
session = boto3.Session(
    aws_access_key_id="YOUR_ACCESS_KEY",
    aws_secret_access_key="YOUR_SECRET_KEY",
    region_name="us-west-2"
)

agent = Agent(
    tools=[...],
    bedrock_client=session.client("bedrock-runtime"),
    dynamodb_client=session.client("dynamodb"),
)
```

### Custom Endpoints

For local development or custom setups:

```python
# Local DynamoDB for testing
agent = Agent(
    tools=[...],
    use_session_memory=True,
    dynamodb_endpoint_url="http://localhost:8000",
)

# Custom Bedrock endpoint (for private deployments)
import boto3
bedrock_client = boto3.client(
    "bedrock-runtime", 
    endpoint_url="https://custom-bedrock-endpoint.example.com"
)

agent = Agent(
    tools=[...],
    bedrock_client=bedrock_client,
)
```

## Configuration Precedence

When multiple configuration methods are used, MinimalAgent follows this precedence (highest to lowest):

1. Direct client objects passed to constructor
2. Explicit parameters passed to constructor
3. AWS profile specified in constructor
4. Environment variables
5. Default AWS credential discovery

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

# Enable session memory after creation
agent.session_manager.use_session_memory = True
agent.session_manager.session_table_name = "new-table-name"
```

## Environment Variables

MinimalAgent respects these environment variables:

```bash
# AWS Credentials
export AWS_ACCESS_KEY_ID="your_access_key"
export AWS_SECRET_ACCESS_KEY="your_secret_key"
export AWS_REGION="us-west-2"
export AWS_PROFILE="my-profile"

# MinimalAgent specific
export MINIMALAGENT_LOG_LEVEL="INFO"
export MINIMALAGENT_MODEL_ID="us.amazon.claude-3-haiku-20240307-v1:0"
```

## Complete Configuration Example

```python
from minimalagent import Agent, tool
from minimalagent.utils.reasoning_display import DisplayConfig
import logging

# Setup custom logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="agent.log"
)
logger = logging.getLogger("agent_logger")

# Custom display configuration
display_config = DisplayConfig(
    thinking_color="cyan",
    tool_name_color="bright_green",
    tool_input_color="yellow",
    tool_result_color="magenta",
    final_thinking_color="blue",
    final_response_color="bright_white",
)

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
    model_id="us.amazon.claude-3-haiku-20240307-v1:0",
    bedrock_region="us-west-2",
    temperature=0.5,
    top_p=1.0,
    max_tokens=2048,
    
    # Display and logging
    show_reasoning=True,
    log_level="INFO",
    logger=logger,
    display_config=display_config,
    display_timestamps=True,
    tool_result_max_length=200,
    
    # Session configuration
    use_session_memory=True,
    session_table_name="search-agent-sessions",
    memory_region="us-west-2",
    session_ttl=3600,  # 1 hour
    real_time_reasoning=True,
    max_reasoning_size=102400,  # 100KB
    
    # AWS configuration
    aws_profile="default",
)

# Run a query
response, reasoning = agent.run(
    "Find information about machine learning",
    session_id="user-session-123"
)
```

## Configuration Best Practices

1. **Start Simple**: Begin with minimal configuration and add options as needed
2. **Match Resources**: Adjust `max_steps` and `max_tokens` based on task complexity
3. **Balance Temperature**: Lower for factual tasks (0.0-0.3), higher for creative tasks (0.7-1.0)
4. **Secure Credentials**: Use environment variables or AWS profiles rather than hardcoded credentials
5. **Test Thoroughly**: Create a testing environment with local DynamoDB before production
6. **Monitor Usage**: Watch your AWS usage, especially with real-time reasoning enabled
7. **Optimize TTL**: Set session TTL appropriate for your application's conversation patterns