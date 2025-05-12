# Session Management

MinimalAgent allows you to create persistent conversations with agents through its built-in session management. Sessions let you maintain context across multiple interactions, store reasoning data, and retrieve past conversations.

## Enabling Session Support

Session management requires Amazon DynamoDB for storage. To enable sessions:

```python
from minimalagent import Agent

agent = Agent(
    tools=[...],
    use_session_memory=True,  # Enable session memory
    session_table_name="my-agent-sessions",  # Optional custom table name
    memory_region="us-west-2",  # AWS region for DynamoDB (can be different from Bedrock region)
    session_ttl=7200,  # Session TTL in seconds (default: 24 hours)
)
```

!!! note
    When session support is enabled, MinimalAgent automatically creates the required DynamoDB table if it doesn't exist.

## Using Sessions in Conversations

To use session memory during agent interactions, provide a `session_id` when calling the `run` method:

```python
# First interaction
response1, reasoning1 = agent.run(
    "What's the weather in Seattle?", 
    session_id="user123"
)

# Later interaction (continues the same conversation)
response2, reasoning2 = agent.run(
    "How about tomorrow?", 
    session_id="user123"  # Same session_id connects the conversations
)
```

!!! tip
    Session IDs can be any string, but they should be consistent for the same conversation. Consider using UUIDs, user IDs, or other unique identifiers.

## Session Persistence

When session support is enabled, MinimalAgent automatically:

1. Stores conversation history in DynamoDB as timestamped snapshots
2. Retrieves the most recent conversation context when continuing a session
3. Includes past interactions in the context for the agent

This allows the agent to reference previous information without requiring the user to repeat it.

!!! note "Storage Pattern"
    MinimalAgent uses an append-only log pattern for session data. Each interaction creates a new timestamped entry with the entire conversation history up to that point. When retrieving conversation history, only the most recent snapshot is used.

## Retrieving Reasoning Data

You can retrieve reasoning data from past interactions:

```python
# Get the most recent reasoning data for a session
reasoning = agent.get_reasoning("user123")

# Get full reasoning history for a session
reasoning_history = agent.get_reasoning_history("user123")
for entry in reasoning_history:
    print(f"Query: {entry.query}")
    print(f"Response: {entry.final_response}")
    print(f"Steps: {entry.total_steps}")
```

## Real-Time Reasoning Updates

MinimalAgent supports real-time updates of reasoning data during agent execution:

```python
agent = Agent(
    tools=[...],
    use_session_memory=True,
    real_time_reasoning=True,  # Enable real-time updates
)
```

With real-time reasoning enabled:
- Each thinking step is saved to DynamoDB as it happens
- Tools invocations are recorded immediately
- External monitoring can observe agent progress

Without real-time reasoning, data is only saved at the end of execution.

## Session TTL Management

Sessions automatically expire after a configurable time to prevent database growth:

```python
agent = Agent(
    tools=[...],
    use_session_memory=True,
    session_ttl=3600,  # Set to 1 hour (in seconds)
)
```

The default TTL is 24 hours. DynamoDB automatically removes expired sessions.

## Custom DynamoDB Configuration

You can customize DynamoDB settings:

```python
agent = Agent(
    tools=[...],
    use_session_memory=True,
    session_table_name="custom-table-name",  # Custom table name
    memory_region="us-east-1",  # Specific AWS region
    dynamodb_endpoint_url="http://localhost:8000",  # For local development with DynamoDB Local
)
```

!!! warning "Permissions Required"
    Ensure your AWS credentials have permissions to create, read, and write to DynamoDB tables.

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

# Retrieve the full conversation history
history = agent.get_reasoning_history(session_id)
print(f"Found {len(history)} interactions in this session")
```

## Best Practices

1. **Consistent Session IDs**: Use the same session ID for related interactions
2. **Appropriate TTL**: Set TTL based on expected conversation duration
3. **Session Cleanup**: Consider implementing a cleanup strategy for unused sessions
4. **Performance**: Be aware that enabling real-time reasoning increases DynamoDB write operations
5. **Cost Management**: Monitor DynamoDB usage if running at scale