# MinimalAgent Documentation

A lightweight agent framework for Amazon Bedrock designed for simplicity and extensibility.

## Key Features

- 🧠 **Reasoning** - Clear tracking of agent's thinking steps
- 🛠️ **Tools** - Simple decorator-based tool definition
- 💾 **Sessions** - Built-in persistent memory with Amazon DynamoDB
- 💻 **Display** - Rich, colorful reasoning display

## Installation

```bash
pip install minimalagent
```

## Quick Example

```python
from minimalagent import Agent, tool

@tool
def add(a: int, b: int) -> int:
    """Add two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of the two numbers
    """
    return a + b

agent = Agent(tools=[add])
response, reasoning = agent.run("What is 5 + 3?")
print(f"Response: {response}")
print(f"Steps taken: {reasoning.total_steps}")
```

## Project Goals

MinimalAgent was created with these goals in mind:

1. **Simplicity** - Minimal boilerplate to get started
2. **Transparency** - Clear visibility into the agent's reasoning process
3. **Extensibility** - Easy to add custom tools and capabilities
4. **Performance** - Lightweight implementation with minimal dependencies

## License

This project is licensed under the MIT License.