# MinimalAgent

A lightweight agent framework for building agentic applications.

## Installation

```bash
pip install minimalagent
```

## AWS Credentials Setup

MinimalAgent requires AWS credentials to access Amazon Bedrock and DynamoDB (if using session persistence).

### Option 1: AWS CLI Configuration (Recommended)

1. Install the AWS CLI: [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

2. Configure AWS credentials:

   ```bash
   aws configure
   ```

3. Follow the prompts to enter your:
   - AWS Access Key ID
   - AWS Secret Access Key
   - Default region (e.g., us-west-2)
   - Default output format (json)

### Option 2: Environment Variables

Set AWS credentials through environment variables:

```bash
# Linux/macOS
export AWS_ACCESS_KEY_ID=your_access_key_id
export AWS_SECRET_ACCESS_KEY=your_secret_access_key
export AWS_REGION=us-west-2

# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="your_access_key_id"
$env:AWS_SECRET_ACCESS_KEY="your_secret_access_key"
$env:AWS_REGION="us-west-2"
```

### Required IAM Permissions

Ensure your AWS credentials have the appropriate IAM permissions:

#### Core Permissions (Always Required)

- `bedrock:InvokeModel` - For calling foundation models

#### Session Persistence Permissions (Only if using session_memory=True)

The following DynamoDB permissions are only required if you enable session memory:

- `dynamodb:CreateTable` - For automatic table creation
- `dynamodb:UpdateTimeToLive` - For setting TTL on session data
- `dynamodb:DescribeTable` - For checking if the table exists
- `dynamodb:PutItem` - For saving session messages
- `dynamodb:Query` - For retrieving session messages

If you don't plan to use session persistence, you can use a more restrictive policy that only includes the Bedrock permissions.

## Quick Start

```python
from minimalagent import Agent, tool

# Define a tool
@tool  # Just use @tool without specifying name
def get_weather(location: str):
    """Get weather for a location.
    
    Args:
        location: City name or coordinates to get weather for
        
    Returns:
        Weather data dictionary
    """
    # Your implementation here
    return {"temperature": 22, "condition": "sunny"}

# Create an agent
agent = Agent(tools=[get_weather])  # Uses default model: us.amazon.nova-pro-v1:0

# Run a query
response = agent.run("What's the weather in San Francisco?")
print(response)
```

### Example with Reasoning Display

```python
from minimalagent import Agent, tool

@tool
def calculate(expression: str):
    """Calculate the result of a mathematical expression.
    
    Args:
        expression: The mathematical expression to evaluate
        
    Returns:
        Dictionary containing the calculation result
    """
    return {"result": eval(expression)}

# Create an agent that shows reasoning
agent = Agent(tools=[calculate], show_reasoning=True)

# Agent will display step-by-step thinking process
response = agent.run("What is 25 * 4 + 10?")
print(response)
```

### Example with Session Memory

```python
from minimalagent import Agent, tool

@tool
def search_database(query: str):
    """Search for information in a database.
    
    Args:
        query: The search query string
        
    Returns:
        Dictionary containing search results
    """
    return {"results": f"Found results for: {query}"}

# Create an agent with session memory
agent = Agent(tools=[search_database], use_session_memory=True)

# First message in conversation
session_id = "user123"  # Use a consistent ID for the same conversation
response = agent.run("Find information about electric cars", session_id=session_id)
print(response)

# Follow-up question - agent remembers previous context
response = agent.run("What about hybrid models?", session_id=session_id)
print(response)
```

## Features

- Simple, intuitive API for creating agents
- Tool decorator for easily adding capabilities
- Control over agent's reasoning process display
- Built on Amazon Bedrock's function calling capabilities
- Tool management (adding and removing tools dynamically)

## Configuration

Initialize the agent with customizable parameters:

```python
agent = Agent(
    tools=[get_weather],
    model_id="us.amazon.nova-pro-v1:0",  # Default model ID
    bedrock_region="us-west-2",          # AWS region for Bedrock
    memory_region="us-east-1",           # Optional different region for DynamoDB (defaults to same as bedrock_region)
    show_reasoning=True,                 # Show the agent's step-by-step reasoning process
    max_steps=5,                         # Maximum number of tool use iterations
    system_prompt="You are a helpful assistant specialized in weather information",  # Optional system prompt
    use_session_memory=True,             # Enable persistent conversations with DynamoDB (default: False)
    session_table_name="my-agent-sessions",  # DynamoDB table for persistent sessions (default: minimalagent-session-table)
    session_ttl=3600                     # Session time-to-live in seconds (default: 1 hour)
)
```

## Logging

MinimalAgent provides control for the agent's reasoning display:

```python
agent = Agent(
    tools=[get_weather],
    show_reasoning=True  # Show the agent's step-by-step reasoning process with colored output
)
```

## Persistent Sessions

MinimalAgent supports persistent conversation memory using DynamoDB:

```python
# Create an agent with session support - Method 1: Explicit opt-in
agent = Agent(
    tools=[get_weather],
    use_session_memory=True,              # Explicitly enable session memory
    session_ttl=7200,                     # 2 hours TTL (optional)
)

# Method 2: Implied opt-in by providing a custom table name
agent = Agent(
    tools=[get_weather],
    session_table_name="weather-agent-sessions",  # Providing a custom table name automatically enables session memory
    session_ttl=7200,                     # 2 hours TTL (optional)
)

# First conversation turn - generates a new session
session_id = "user123"  # You can use any string as session ID
response1 = agent.run("What's the weather in Seattle?", session_id=session_id)

# Later conversation turns - continues the same session
response2 = agent.run("How about tomorrow?", session_id=session_id)  # Remembers previous context
```

Session features:

- Automatic DynamoDB table creation if it doesn't exist
- Implied opt-in when specifying a custom table name
- Configurable session TTL (time-to-live)
- Seamless conversation context preservation
- Sessions are stored as single items in DynamoDB for efficiency

## Tool Management

MinimalAgent allows dynamic management of tools:

```python
from minimalagent import Agent, tool

# Create tools
@tool
def tool_a(param: str):
    """Tool A description"""
    return {"result": f"Processed {param}"}

@tool
def tool_b(param: str):
    """Tool B description"""
    return {"result": f"Processed {param}"}

# Create agent with initial tools
agent = Agent(tools=[tool_a])

# Add more tools later
agent.add_tools([tool_b])

# Run the agent with both tools available
response = agent.run("Use tool B to process data")

# Clear all tools
agent.clear_tools()

# Run with no tools available
response = agent.run("Can you process this data?")
```

## Creating Custom Tools

MinimalAgent makes tool creation simple with two approaches - both using the `@tool` decorator:

### Simple Approach: Docstring-Based Tools (Recommended)

Just add the `@tool` decorator and well-structured docstrings:

```python
from minimalagent import Agent, tool

@tool  # No parameters needed - everything is extracted from the docstring
def get_weather(location: str, units: str = "metric") -> dict:
    """Get current weather information for a location.

    Args:
        location: City name or coordinates to get weather for
        units: Measurement units (metric or imperial)

    Returns:
        Dict containing weather information
    """
    # Your implementation here
    weather_data = {"temperature": 22.5, "condition": "sunny", "location": location}

    # Convert to imperial if requested
    if units == "imperial":
        weather_data["temperature"] = round(weather_data["temperature"] * 9/5 + 32)

    return weather_data
```

The decorator automatically extracts:

- Tool name from the function name
- Description from the first line of the docstring
- Parameter descriptions from the Args section

### Advanced Approach: Explicit Configuration

For more control, you can override specific aspects:

```python
@tool(
    name="weather_lookup",  # Override the default name
    description="Get weather conditions for any location",  # Override description
    param_descriptions={
        "location": "Location name or geographic coordinates"  # Override specific parameter descriptions
    }
)
def get_weather(location: str, units: str = "metric") -> dict:
    """This docstring description will be overridden by the description parameter.

    Args:
        location: This description will be overridden
        units: This description will still be used since it wasn't overridden

    Returns:
        Weather data dictionary
    """
    # Implementation...
    return {"temperature": 22, "condition": "sunny", "location": location}
```

### Docstring Format Requirements

Your docstrings should follow this simple structure:

```python
@tool
def my_tool(param1: str, param2: int = 0) -> dict:
    """First line becomes the tool description.

    Any text here becomes the long description.

    Args:
        param1: Description for first parameter
        param2: Description for second parameter

    Returns:
        Description of what the tool returns
    """
    # Implementation...
```

The requirements are:

1. First line: Clear description of what the tool does
2. Args section: Parameter descriptions in Google-style format
3. Type annotations for all parameters (str, int, etc.)

### Tool Logging

Tools are completely independent of the agent's internal logging system. To configure tool logging, use standard Python logging configuration:

```python
# Tool developers can control their own logging
logging.basicConfig(level=logging.INFO)

# Or configure specific loggers
logging.getLogger("my_tools").setLevel(logging.DEBUG)
```

## Security Considerations

When using MinimalAgent, keep these security considerations in mind:

1. **DynamoDB Data Storage**: When session persistence is enabled, conversation data is stored in DynamoDB without encryption. For sensitive applications, consider enabling [DynamoDB encryption](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/encryption.at-rest.html) or implement client-side encryption.

2. **Input Validation**: The `session_id` parameter is validated to prevent injection attacks. Only alphanumeric characters, dashes, and underscores are allowed, with a maximum length of 128 characters.

3. **Data Retention**: Session data has a configurable Time-to-Live (TTL), but be mindful of how long sensitive conversation data is stored in DynamoDB.

4. **Rate Limiting**: There is no built-in rate limiting for Bedrock API calls. Consider implementing rate limiting in your application to prevent excessive costs.

5. **System Prompts**: Be careful with the content of system prompts, as they can influence the model behavior. Avoid including sensitive data in prompts.

## License

MIT
