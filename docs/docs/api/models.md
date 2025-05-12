# Data Models API Reference

MinimalAgent provides data models for representing reasoning processes, tool usage, and other aspects of agent execution.

## Reasoning Class

The Reasoning class represents the complete reasoning process for an agent interaction.

::: minimalagent.models.Reasoning
    options:
      show_root_heading: true
      show_source: false

## ReasoningStep Class

The ReasoningStep class represents a single step in the agent's reasoning process.

::: minimalagent.models.ReasoningStep
    options:
      show_root_heading: true
      show_source: false

## ToolData Class

The ToolData class contains information about a tool execution.

::: minimalagent.models.ToolData
    options:
      show_root_heading: true
      show_source: false

## Usage Examples

### Working with Reasoning Objects

```python
from minimalagent import Agent, tool
from minimalagent.models import Reasoning, ReasoningStep, ToolData

# Run an agent and get reasoning
agent = Agent(tools=[some_tool])
response, reasoning = agent.run("What's the weather?")

# Access reasoning data
print(f"Query: {reasoning.query}")
print(f"Steps taken: {reasoning.total_steps}")

# Check if reasoning was truncated
if reasoning.exceeded_size_limit:
    print("Warning: Reasoning data was truncated due to size limits")

# Loop through steps
for step in reasoning.steps:
    print(f"Step {step.step_number}: {step.thinking}")
    
    # Access tools used in this step
    for tool in step.tools:
        print(f"  Tool: {tool.name}")
        print(f"  Inputs: {tool.inputs}")
        print(f"  Result: {tool.result}")
```

### Creating Custom Reasoning Objects

```python
from minimalagent.models import Reasoning, ReasoningStep, ToolData
import time

# Create tool data
tool_data = ToolData(
    name="get_weather",
    inputs={"location": "Seattle"},
    result={"temperature": 72, "conditions": "sunny"}
)

# Create a reasoning step
step = ReasoningStep(
    step_number=1,
    timestamp=int(time.time()),
    thinking="I need to check the weather in Seattle",
    tools=[tool_data]
)

# Create a reasoning object
reasoning = Reasoning(
    session_id="user123",
    query="What's the weather in Seattle?",
    steps=[step],
    total_steps=1,
    final_thinking="The weather in Seattle is sunny with a temperature of 72 degrees.",
    final_response="It's currently 72°F and sunny in Seattle."
)

# Convert to dictionary (for serialization)
reasoning_dict = reasoning.to_dict()

# Create from dictionary (after deserialization)
reconstructed = Reasoning.from_dict(reasoning_dict)
```