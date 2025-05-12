# Understanding Reasoning Data

When you run an agent using MinimalAgent, you get back both the text response and a `reasoning` object containing detailed information about the agent's process. This guide explains the key data structures you'll work with.

## The Reasoning Object

The `reasoning` object gives you access to everything that happened during the agent's execution:

```python
from minimalagent import Agent, tool

@tool
def calculate(expression: str) -> dict:
    """Calculate a math expression."""
    result = eval(expression)
    return {"result": result}

agent = Agent(tools=[calculate])
response, reasoning = agent.run("What's 25 * 4?")

print(f"Query: {reasoning.query}")
print(f"Final response: {reasoning.final_response}")
print(f"Steps taken: {reasoning.total_steps}")
```

## Key Properties

The most important properties you'll use:

| Property | Description |
|----------|-------------|
| `query` | The original question asked |
| `final_response` | The agent's final answer |
| `total_steps` | Number of steps the agent took |
| `steps` | List of all steps, including thinking and tool usage |

## Examining Steps and Tool Usage

Each step in the reasoning process contains information about what the agent was thinking and which tools it used:

```python
# Loop through each step
for step in reasoning.steps:
    print(f"\nStep {step.step_number} thinking:")
    print(step.thinking)
    
    # Show tools used in this step
    for tool in step.tools:
        print(f"Tool: {tool.name}")
        print(f"Inputs: {tool.inputs}")
        print(f"Result: {tool.result}")
```

## Practical Example: Analyzing Agent Behavior

Here's how to analyze how your agent solved a problem:

```python
from minimalagent import Agent, tool

@tool
def search_database(query: str) -> list:
    """Search the database for information."""
    # Simulated database search
    return [{"id": 1, "result": f"Information about {query}"}]

@tool
def format_output(items: list) -> dict:
    """Format items for display."""
    return {"formatted": [f"• {item['result']}" for item in items]}

# Create agent with both tools
agent = Agent(tools=[search_database, format_output])

# Run a query
response, reasoning = agent.run("Find information about climate change")

# Analyze tool usage
tool_usage = {}
for step in reasoning.steps:
    for tool in step.tools:
        tool_name = tool.name
        if tool_name not in tool_usage:
            tool_usage[tool_name] = 0
        tool_usage[tool_name] += 1

print("Tool usage summary:")
for tool, count in tool_usage.items():
    print(f"- {tool}: used {count} times")

# Check execution time if timestamps are available
if hasattr(reasoning, 'start_timestamp') and hasattr(reasoning, 'end_timestamp'):
    execution_time = reasoning.end_timestamp - reasoning.start_timestamp
    print(f"Total execution time: {execution_time} seconds")
```

## Working with Session History

When using session management, you can retrieve and analyze past reasoning:

```python
# Get the most recent reasoning for a session
latest_reasoning = agent.get_reasoning("user123")

# Get all reasoning history for a session
history = agent.get_reasoning_history("user123")

# Show evolution of responses
print("Response history:")
for i, entry in enumerate(history):
    print(f"{i+1}: Query: {entry.query}")
    print(f"   Response: {entry.final_response}")

# Count total tools used across the session
total_tools = 0
for entry in history:
    for step in entry.steps:
        total_tools += len(step.tools)

print(f"Total tools used in session: {total_tools}")
```

## Debugging with Reasoning Data

The reasoning data is invaluable for debugging agent behavior:

```python
# Check for tool errors
for step in reasoning.steps:
    for tool in step.tools:
        if "error" in str(tool.result).lower():
            print(f"ERROR in tool {tool.name}: {tool.result}")

# Examine which tools were considered but not used
for step in reasoning.steps:
    thinking = step.thinking.lower()
    if "consider" in thinking and "tool" in thinking:
        print(f"Step {step.step_number} considered tools: {thinking}")
```

This understanding of reasoning data helps you analyze how your agent works, identify issues, and improve its effectiveness.