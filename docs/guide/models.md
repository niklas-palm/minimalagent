# Understanding Data Models

MinimalAgent uses several data models to represent reasoning processes, tool usage, and agent states. This guide explains these models in detail and shows how to work with them effectively.

## Core Data Models

MinimalAgent's core data models include:

- **Reasoning**: Represents an entire reasoning process
- **ReasoningStep**: Represents a single step in the reasoning process
- **ToolData**: Contains information about a tool invocation
- **SessionMessage**: Represents a message in a conversation session

## Reasoning Model

The `Reasoning` model tracks an agent's complete reasoning process:

```python
from minimalagent import Agent, tool
from minimalagent.models import Reasoning

@tool
def greet(name: str) -> dict:
    """Greet a person."""
    return {"greeting": f"Hello, {name}!"}

agent = Agent(tools=[greet])
response, reasoning = agent.run("Say hello to Jane")

# Access reasoning data
print(f"Query: {reasoning.query}")
print(f"Steps: {reasoning.total_steps}")
print(f"Final response: {reasoning.final_response}")
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `session_id` | `str` | Identifier for the session (if using sessions) |
| `query` | `str` | The original query sent to the agent |
| `steps` | `list[ReasoningStep]` | List of reasoning steps |
| `total_steps` | `int` | Total number of steps in the reasoning |
| `final_thinking` | `str` | Agent's final thinking process |
| `final_response` | `str` | Agent's final response |
| `start_timestamp` | `int` | Unix timestamp when reasoning started |
| `end_timestamp` | `int` | Unix timestamp when reasoning completed |
| `exceeded_size_limit` | `bool` | Whether reasoning was truncated |

### Working with Reasoning Data

```python
# Check execution time
execution_time = reasoning.end_timestamp - reasoning.start_timestamp
print(f"Execution time: {execution_time} seconds")

# Check if reasoning was complete or truncated
if reasoning.exceeded_size_limit:
    print("Warning: Reasoning was truncated due to size limits")

# Convert to dictionary for storage/serialization
reasoning_dict = reasoning.to_dict()

# Recreate from dictionary after loading
loaded_reasoning = Reasoning.from_dict(reasoning_dict)
```

## ReasoningStep Model

Each `ReasoningStep` represents a single step in the agent's thinking process:

```python
# Accessing reasoning steps
for step in reasoning.steps:
    print(f"Step {step.step_number}")
    print(f"Thinking: {step.thinking}")
    print(f"Timestamp: {step.timestamp}")
    print(f"Tools used: {len(step.tools)}")
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `step_number` | `int` | The order of this step (1-indexed) |
| `thinking` | `str` | The agent's thoughts for this step |
| `tools` | `list[ToolData]` | List of tools invoked in this step |
| `timestamp` | `int` | Unix timestamp when this step occurred |

## ToolData Model

The `ToolData` model stores information about tool invocations:

```python
# Loop through steps and extract tool usage
for step in reasoning.steps:
    for tool in step.tools:
        print(f"Tool name: {tool.name}")
        print(f"Inputs: {tool.inputs}")
        print(f"Result: {tool.result}")
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `name` | `str` | Name of the tool invoked |
| `inputs` | `dict` | Dictionary of inputs provided to the tool |
| `result` | `dict` | Dictionary containing tool results |
| `error` | `str` | Error message (if tool execution failed) |

## Creating Custom Model Instances

You can manually create model instances for testing or advanced scenarios:

```python
from minimalagent.models import Reasoning, ReasoningStep, ToolData
import time

# Create tool data
tool_data = ToolData(
    name="multiply",
    inputs={"a": 5, "b": 3},
    result={"result": 15}
)

# Create a reasoning step
step = ReasoningStep(
    step_number=1,
    timestamp=int(time.time()),
    thinking="I need to multiply 5 and 3",
    tools=[tool_data]
)

# Create a reasoning object
reasoning = Reasoning(
    session_id="test-session",
    query="What is 5 times 3?",
    steps=[step],
    total_steps=1,
    final_thinking="I used the multiply tool to calculate 5 × 3 = 15",
    final_response="The result is 15.",
    start_timestamp=int(time.time()) - 10,
    end_timestamp=int(time.time())
)
```

## Working with Session Messages

When using session memory, MinimalAgent tracks messages in the conversation:

```python
from minimalagent.models import SessionMessage

# Session messages include roles and content
user_message = SessionMessage(
    role="user",
    content="What's the weather in Seattle?"
)

assistant_message = SessionMessage(
    role="assistant",
    content="It's currently 55°F and rainy in Seattle."
)

# Messages are automatically managed by the session system
# You don't typically need to create them manually
```

## Size and Storage Considerations

MinimalAgent automatically handles serialization and storage of reasoning data:

```python
# Check the serialized size
reasoning_dict = reasoning.to_dict()
import json
serialized = json.dumps(reasoning_dict)
print(f"Serialized reasoning size: {len(serialized)} bytes")

# MinimalAgent automatically truncates reasoning if it exceeds limits
# You can set a custom size limit (in bytes)
agent = Agent(
    tools=[...],
    max_reasoning_size=51200,  # 50 KB limit
)
```

!!! warning
    Very large reasoning objects may impact performance and storage costs.

## Troubleshooting with Model Data

Models provide valuable debugging information:

```python
# Analyzing steps for debugging
for step in reasoning.steps:
    # Check timestamp to identify slow steps
    print(f"Step {step.step_number} at {step.timestamp}")
    
    # Identify tool failures
    for tool in step.tools:
        if "error" in tool.result:
            print(f"Tool {tool.name} failed: {tool.result['error']}")
        
    # Look for unexpected outputs
    print(step.thinking)
```

## Combining with Sessions

Data models integrate with session management:

```python
# Run with session
agent = Agent(tools=[...], use_session_memory=True)
response, reasoning = agent.run("Hello", session_id="user123")

# Later, retrieve reasoning from storage
stored_reasoning = agent.get_reasoning("user123")

# Compare with in-memory reasoning
assert reasoning.query == stored_reasoning.query
assert reasoning.final_response == stored_reasoning.final_response
```

## Complete Example

```python
from minimalagent import Agent, tool
from minimalagent.models import Reasoning
import json

@tool
def calculate(expression: str) -> dict:
    """Calculate a math expression."""
    try:
        result = eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

# Create agent
agent = Agent(tools=[calculate])

# Run a query
response, reasoning = agent.run("What is 15 * 7 + 22?")

# Show complete reasoning structure
print("Reasoning structure:")
print(f"Query: {reasoning.query}")
print(f"Steps: {reasoning.total_steps}")

for i, step in enumerate(reasoning.steps):
    print(f"\nStep {i+1}:")
    print(f"Thinking: {step.thinking[:100]}...")
    
    for tool in step.tools:
        print(f"Tool: {tool.name}")
        print(f"Inputs: {tool.inputs}")
        print(f"Result: {tool.result}")

print(f"\nFinal thinking: {reasoning.final_thinking[:100]}...")
print(f"Final response: {reasoning.final_response}")

# Save reasoning to file for later analysis
with open("reasoning_example.json", "w") as f:
    json.dump(reasoning.to_dict(), f, indent=2)
```