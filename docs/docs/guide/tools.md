# Creating Custom Tools

Tools allow your agent to interact with external systems and APIs. This guide shows you how to define and use custom tools with MinimalAgent.

!!! tip
    Tools are automatically documented from your docstrings, so write good docstrings!

## Basic Tool Definition

Tools are created using the `@tool` decorator:

```python
from minimalagent import tool

@tool
def get_weather(location: str, units: str = "metric") -> dict:
    """Get weather information for a location.
    
    Args:
        location: City name or location
        units: Units to use (metric or imperial)
        
    Returns:
        Weather data dictionary
    """
    # Add implementation here
    return {"temperature": 22, "conditions": "sunny"}
```

## Tool Parameters

Tools support various parameter types:

| Type | Example | Notes |
| ---- | ------- | ----- |
| `str` | `name: str` | Text values |
| `int` | `count: int` | Integers |
| `float` | `temperature: float` | Decimal numbers |
| `bool` | `enabled: bool` | True/False values |
| `list` | `items: list` | Lists of items |
| `dict` | `config: dict` | Key-value mappings |

## Adding Tools to an Agent

```python
# Define your tools
@tool
def tool_a(param: str): 
    """A sample tool."""
    return {"result": param}

@tool 
def tool_b(param: int):
    """Another sample tool."""
    return {"result": param * 2}

# Add at initialization
agent = Agent(tools=[tool_a, tool_b])

# Or add later
agent = Agent()
agent.add_tools([tool_a, tool_b])
```

## Customizing Tool Documentation

You can override the automatic documentation:

```python
@tool(
    name="custom_weather",
    description="Get weather forecast for any location",
    param_descriptions={
        "location": "City name, postal code, or coordinates",
        "units": "Unit system: 'metric' (°C) or 'imperial' (°F)"
    }
)
def get_weather(location: str, units: str = "metric"):
    # Implementation here
    pass
```

## Error Handling in Tools

Tools should handle errors gracefully:

```python
@tool
def divide(a: float, b: float) -> float:
    """Divide two numbers.
    
    Args:
        a: Numerator
        b: Denominator
        
    Returns:
        Result of division
    """
    try:
        if b == 0:
            return {"error": "Cannot divide by zero"}
        return {"result": a / b}
    except Exception as e:
        return {"error": str(e)}
```

## Best Practices

1. **Clear docstrings**: Write clear descriptions and parameter documentation
2. **Strong typing**: Use type hints for all parameters
3. **Return dictionaries**: Always return a dictionary with meaningful keys
4. **Handle errors**: Catch exceptions and return structured error responses
5. **Atomic functionality**: Each tool should do one thing well

## Example: Web Search Tool

```python
import requests

@tool
def web_search(query: str, results_count: int = 5) -> dict:
    """Search the web for information.
    
    Args:
        query: Search query string
        results_count: Number of results to return (max 10)
        
    Returns:
        Dictionary containing search results
    """
    try:
        # Limit results to reasonable number
        results_count = min(max(1, results_count), 10)
        
        # In a real implementation, you would call a search API
        # This is a placeholder implementation
        response = {
            "results": [
                {"title": f"Result {i+1} for {query}", 
                 "snippet": f"This is a sample result for {query}"}
                for i in range(results_count)
            ],
            "total": results_count
        }
        
        return response
    except Exception as e:
        return {"error": str(e), "results": []}
```