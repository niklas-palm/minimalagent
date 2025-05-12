# Session Management

MinimalAgent provides built-in session management to maintain conversation context and track reasoning across multiple interactions.

## Quick Start

Enable session support with just one parameter:

```python
agent = Agent(use_session_memory=True)

# First interaction
response1 = agent.run("What's the weather in Seattle?", session_id="user123")

# Later interaction (remembers context)
response2 = agent.run("What about tomorrow?", session_id="user123")
```

## What Sessions Provide

- **Conversation Memory**: Agent remembers previous messages and context
- **Reasoning Storage**: Track the agent's thinking process over time
- **Persistence**: Data stored in DynamoDB with automatic TTL

## Configuration Options

```python
agent = Agent(
    # Basic session settings
    use_session_memory=True,             # Enable session persistence
    session_ttl=3600,                    # Session TTL in seconds (default: 1 hour)
    
    # Advanced settings
    session_table_name="my-sessions",    # Custom DynamoDB table name
    real_time_reasoning=True,            # Update reasoning during execution
    memory_region="us-east-1",           # AWS region for DynamoDB
)
```

## Retrieving Reasoning and Tool Invocation History

A key benefit of session management is the ability to retrieve detailed reasoning and tool usage history. This is particularly valuable for debugging, monitoring, or analyzing how the agent performed complex multi-step tasks:

```python
# Get the most recent reasoning data for a session
reasoning = agent.get_reasoning("user123")
print(f"Query: {reasoning.query}")
print(f"Response: {reasoning.final_response}")

# Examine tool usage from the most recent interaction
print(f"The agent took {reasoning.total_steps} steps to answer")
for step in reasoning.steps:
    print(f"\nStep {step.step_number} thinking: {step.thinking}")
    
    # Analyze all tools used in this step
    for tool in step.tools:
        print(f"Tool used: {tool.name}")
        print(f"Tool inputs: {tool.inputs}")
        print(f"Tool result: {tool.result}")

# Get complete reasoning history across all interactions
reasoning_history = agent.get_reasoning_history("user123")
print(f"Found {len(reasoning_history)} interactions in this session")

# Analyze all tool invocations across all interactions
for i, interaction in enumerate(reasoning_history):
    print(f"\nInteraction {i+1}: {interaction.query}")
    print(f"Total steps: {interaction.total_steps}")
    
    for step in interaction.steps:
        for tool in step.tools:
            print(f"Tool: {tool.name}, Inputs: {tool.inputs}")
```

**Note**: `get_reasoning_history()` retrieves reasoning objects with complete tool invocation data, allowing you to track exactly what tools were called, with what parameters, and what results they returned across an entire session.

## Real-Time Reasoning and Tool Tracking

Enable real-time reasoning to track the agent's thinking process and tool invocations as they happen:

```python
agent = Agent(
    use_session_memory=True,
    real_time_reasoning=True
)
```

With real-time updates, each thinking step and tool use is written to DynamoDB immediately, enabling:

1. **Live Tool Monitoring**: See tools being called in real-time with their parameters and results
2. **Complex Task Tracking**: Monitor multi-step processes that might take significant time
3. **External Monitoring**: Build dashboards or monitoring systems by polling the database

### Example: Monitoring Long-Running Operations

This is especially valuable for applications with long-running operations:

```python
# In your application
agent = Agent(
    tools=[long_running_tool, search_database, complex_analysis],
    use_session_memory=True,
    real_time_reasoning=True
)

# Start a complex operation
agent.run("Analyze the latest data and generate a comprehensive report", session_id="report-task")

# In a separate monitoring application
import time

def monitor_progress(session_id):
    while True:
        reasoning = agent.get_reasoning(session_id)
        
        # Show completed steps
        print(f"Completed {len(reasoning.steps)} of {reasoning.total_steps} steps")
        
        # Show tools used so far
        for step in reasoning.steps:
            for tool in step.tools:
                print(f"Tool used: {tool.name} with inputs: {tool.inputs}")
                print(f"Result: {tool.result}")
        
        time.sleep(5)  # Poll every 5 seconds
```

## Session Storage Details

Sessions are stored in DynamoDB with:
- Automatic table creation
- TTL-based expiration
- Partition key: `messages#{session_id}` or `reasoning#{session_id}`
- Sort key: Timestamp

### DynamoDB Table Structure

MinimalAgent uses a single-table design with the following structure:

| Attribute | Type | Description |
|-----------|------|-------------|
| `pk` | String | Partition key with prefix: `messages#{session_id}` or `reasoning#{session_id}` |
| `sk` | Number | Sort key using timestamp (Unix epoch) |
| `expiration_time` | Number | TTL attribute for automatic deletion |
| `messages` | String | JSON string of messages (only in message items) |
| `reasoning` | String | JSON string of reasoning data (only in reasoning items) |

### Bring Your Own DynamoDB Table

You can use your own pre-created DynamoDB table instead of having MinimalAgent create one for you. This is useful for:

- Infrastructure-as-code deployments
- Custom resource controls (provisioned capacity, encryption, etc.)
- Shared tables across multiple applications
- Custom backup policies

To use your own table, it must follow this schema:

```yaml
# AWS SAM/CloudFormation example
Resources:
  AgentSessionTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: my-custom-session-table
      BillingMode: PAY_PER_REQUEST  # Or use provisioned capacity
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S  # String type
        - AttributeName: sk
          AttributeType: N  # Number type
      KeySchema:
        - AttributeName: pk
          KeyType: HASH  # Partition key
        - AttributeName: sk
          KeyType: RANGE  # Sort key
      TimeToLiveSpecification:
        AttributeName: expiration_time
        Enabled: true
```

Then, tell the agent to use your custom table:

```python
agent = Agent(
    tools=[...],
    use_session_memory=True,
    session_table_name="my-custom-session-table",  # Your custom table name
)
```

#### AWS CloudFormation/SAM Example

Here's a CloudFormation/SAM template for creating just the DynamoDB table:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  AgentSessionTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: my-agent-sessions  # Choose your table name
      BillingMode: PAY_PER_REQUEST  # Or use provisioned capacity
      AttributeDefinitions:
        - AttributeName: pk
          AttributeType: S  # String type for partition key
        - AttributeName: sk
          AttributeType: N  # Number type for sort key
      KeySchema:
        - AttributeName: pk
          KeyType: HASH    # Partition key
        - AttributeName: sk
          KeyType: RANGE   # Sort key
      TimeToLiveSpecification:
        AttributeName: expiration_time
        Enabled: true
      # Optional: Add point-in-time recovery
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      # Optional: Add tags
      Tags:
        - Key: Project
          Value: MinimalAgent

Outputs:
  AgentTableName:
    Description: Session DynamoDB Table Name
    Value: !Ref AgentSessionTable
```

To use this table with MinimalAgent, simply reference its name:

```python
from minimalagent import Agent, tool

@tool
def example_tool(param: str) -> dict:
    """Example tool functionality."""
    return {"result": f"Processed {param}"}

agent = Agent(
    tools=[example_tool],
    use_session_memory=True,
    session_table_name="my-agent-sessions"  # Match the table name from CloudFormation
)
```

## Best Practices

1. Use consistent session IDs for related interactions
2. Set appropriate TTL based on expected conversation duration
3. Monitor DynamoDB usage if running at scale

## Complete Example

Here's a complete example of session management:

```python
from minimalagent import Agent, tool
import uuid

@tool
def answer_question(question: str) -> dict:
    """Answer a simple question."""
    return {"answer": f"The answer to '{question}' is 42."}

# Create agent with sessions enabled
agent = Agent(
    tools=[answer_question],
    use_session_memory=True,
    show_reasoning=True,
)

# Generate session ID (or use a user ID in a real application)
session_id = str(uuid.uuid4())

# First interaction
response1, reasoning1 = agent.run(
    "What is the meaning of life?", 
    session_id=session_id
)

# Second interaction (referencing the first)
response2, reasoning2 = agent.run(
    "Can you elaborate on that?", 
    session_id=session_id
)

# Retrieve the reasoning history
history = agent.get_reasoning_history(session_id)
print(f"Found {len(history)} interactions in this session")
```