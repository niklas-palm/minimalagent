# MinimalAgent

A lightweight agent framework for building agentic applications with Amazon Bedrock.

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

## Installation

```bash
pip install minimalagent
```

## Key Features

- **Simple API**: Intuitive design with minimal boilerplate
- **Tool-first approach**: Easy tool creation with docstring parsing
- **Built-in session memory**: Persistent conversations via DynamoDB
- **Step-by-step reasoning**: Visibility into the agent's thought process
- **Configurable logging**: Separate display and debugging channels
- **AWS-native**: Uses Amazon Bedrock for function calling

## Core Concepts

### Tools

Tools give your agent capabilities. Simply decorate functions with `@tool`:

```python
@tool
def search_database(query: str, limit: int = 10) -> list:
    """Search the database for records matching the query.
    
    Args:
        query: The search term
        limit: Maximum number of results
        
    Returns:
        List of matching records
    """
    # Your implementation here
    return [{"id": 1, "name": query}]
```

Tools can be added or removed dynamically:

```python
# Add tools after initialization
agent.add_tools([another_tool])

# Remove all tools
agent.clear_tools()
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

### Reasoning Process

Access the agent's step-by-step thinking:

```python
response, reasoning = agent.run("Calculate 25 * 4 + 10")

# Access reasoning data
print(f"Query: {reasoning['query']}")
print(f"Steps: {reasoning['total_steps']}")
for step in reasoning['steps']:
    print(f"Step {step['step_number']} thinking: {step['thinking']}")
```

## Common Usage Patterns

### Configuring Display and Logging

Control both colorized output and standard logging:

```python
# Interactive development - show colorized reasoning and debug logs
agent = Agent(show_reasoning=True, log_level="DEBUG")

# Production with detailed logs - no colorized output but informative logs
agent = Agent(show_reasoning=False, log_level="INFO")

# Production deployment - no display, only warnings and errors
agent = Agent(show_reasoning=False, log_level="WARNING")  # Default
```

### Creating Tools with Docstrings

MinimalAgent automatically extracts tool information from docstrings:

```python
@tool  # Simple approach - everything from docstring
def calculate(expression: str):
    """Calculate the result of a mathematical expression.
    
    Args:
        expression: The mathematical expression to evaluate
        
    Returns:
        Dict containing the calculation result
    """
    return {"result": eval(expression)}
```

For more control, override specific aspects:

```python
@tool(
    name="weather_lookup",  # Override default name
    description="Get weather conditions",  # Override description
    param_descriptions={
        "location": "Geographic location"  # Override specific parameter
    }
)
def get_weather(location: str, units: str = "metric") -> dict:
    # Implementation...
    return {"temperature": 22, "condition": "sunny"}
```

### Real-Time Reasoning Updates

Track the agent's thinking process during execution:

```python
agent = Agent(
    use_session_memory=True,
    real_time_reasoning=True  # Enable real-time updates
)

# Run the agent
response, reasoning = agent.run("Search for climate change", session_id="user123")

# Retrieve reasoning for just the most recent interaction
latest_reasoning = agent.get_reasoning(session_id="user123") 

# Retrieve complete reasoning history for all interactions
all_reasoning = agent.get_reasoning_history(session_id="user123")
```

With `real_time_reasoning=True`, reasoning data is updated in DynamoDB continuously during execution, not just at the end of the process. This allows you to monitor the agent's thought process in real-time through a separate interface that polls the database.

## Configuration Reference

Initialize the agent with any of these parameters:

```python
agent = Agent(
    # Tool Configuration
    tools=[tool_1, tool_2],           # List of tool functions
    
    # Display and Logging
    show_reasoning=True,              # Show colorized reasoning process
    log_level="WARNING",              # Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    # Model Configuration
    model_id="us.amazon.nova-pro-v1:0", # Amazon Bedrock model
    system_prompt="You are a helpful assistant...", # Custom system prompt
    
    # Session Configuration
    use_session_memory=True,          # Enable persistent conversations
    session_table_name="my-sessions", # Custom DynamoDB table name
    session_ttl=3600,                 # Session TTL in seconds (default: 1 hour)
    real_time_reasoning=True,         # Update reasoning during execution
    
    # AWS Configuration
    bedrock_region="us-west-2",       # AWS region for Bedrock
    memory_region="us-east-1",        # AWS region for DynamoDB (defaults to bedrock_region)
)
```

### Parameter Reference

| Parameter           | Type       | Default Value           | Description                 | Validation/Notes |
|---------------------|------------|-------------------------|-----------------------------|------------------|
| `tools`             | List       | `None`                  | Tool functions decorated with `@tool` | Functions must be decorated with `@tool` |
| `max_steps`         | int        | `5`                     | Maximum tool use iterations | Must be > 0 |
| `show_reasoning`    | bool       | `True`                  | Show colorized reasoning output | - |
| `log_level`         | str        | `"WARNING"`             | Standard logging level | Must be one of: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" |
| `model_id`          | str        | `"us.amazon.nova-pro-v1:0"` | Amazon Bedrock model ID | Must be a model that supports function calling |
| `bedrock_region`    | str        | `"us-west-2"`           | AWS region for Bedrock | Must be a valid AWS region where Bedrock is available |
| `memory_region`     | str or None | Same as `bedrock_region` | AWS region for DynamoDB | Must be a valid AWS region where DynamoDB is available |
| `system_prompt`     | str        | `""`                    | System prompt for the model | - |
| `use_session_memory` | bool      | `False`                 | Enable persistent sessions | Auto-enabled if custom `session_table_name` is provided |
| `real_time_reasoning` | bool     | `False`                | Update reasoning during execution | Only works when `use_session_memory=True` |
| `session_table_name` | str       | `"minimalagent-session-table"` | DynamoDB table name | Alphanumeric with hyphens; Providing custom name auto-enables `use_session_memory` |
| `session_ttl`       | int        | `3600` (1 hour)         | Session TTL in seconds | Must be > 0 |

## AWS Setup

MinimalAgent requires AWS credentials for accessing Amazon Bedrock and DynamoDB.

### Option 1: AWS CLI Configuration (Recommended)

1. Install and configure the AWS CLI:
   ```bash
   aws configure
   ```

2. Follow the prompts to enter your credentials and default region.

### Option 2: Environment Variables

```bash
# Linux/macOS
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_REGION=us-west-2
```

### Required IAM Permissions

- `bedrock:InvokeModel` - Required for all uses
- DynamoDB permissions (only if using sessions):
  - `dynamodb:CreateTable`, `dynamodb:UpdateTimeToLive`
  - `dynamodb:DescribeTable`, `dynamodb:PutItem`, `dynamodb:Query`

## DynamoDB Implementation

### Single-Table Design

When using session memory, MinimalAgent employs a single-table design pattern storing different entity types in the same table:

#### Table Schema

| Attribute         | Type   | Description                                      |
|-------------------|--------|--------------------------------------------------|
| `pk`              | String | Partition key with entity type prefix            |
| `sk`              | Number | Sort key using timestamp                         |
| `expiration_time` | Number | TTL attribute for automatic data expiration      |
| `messages`        | String | JSON string of conversation (only in message items) |
| `reasoning`       | String | JSON string of reasoning data (only in reasoning items) |

#### Entity Types

The table stores two distinct types of items:

| Entity Type          | `pk` Pattern           | `sk` Value | `messages` | `reasoning` | Description                     |
|----------------------|------------------------|------------|------------|-------------|---------------------------------|
| Conversation Messages | `messages#{session_id}`| Timestamp  | ✓          | -           | Full conversation history       |
| Agent Reasoning       | `reasoning#{session_id}`| Timestamp  | -          | ✓           | Agent's thinking process & tools |

### Bring Your Own Table

If you prefer to create your own DynamoDB table (via CloudFormation, SAM, etc.), you must ensure it follows this schema:

```yaml
# AWS SAM example
Resources:
  AgentSessionTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: my-agent-sessions  # Name this whatever you prefer
      BillingMode: PAY_PER_REQUEST  # Or use provisioned capacity
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S
        - AttributeName: sk
          AttributeType: N
      KeySchema:
        - AttributeName: pk
          KeyType: HASH
        - AttributeName: sk
          KeyType: RANGE
      TimeToLiveSpecification:
        AttributeName: expiration_time
        Enabled: true
```

To use your custom table:

```python
agent = Agent(
    tools=[get_weather],
    session_table_name="my-agent-sessions",  # Your custom table name
    use_session_memory=True                  # Enable session memory
)
```

## Security Considerations

- Session data is stored in DynamoDB without encryption by default
- Session IDs are validated to prevent injection attacks
- Session data automatically expires based on the configured TTL
- Consider implementing rate limiting for production use

## License

MIT