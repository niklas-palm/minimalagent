# Basic Usage Examples

These examples demonstrate common patterns for using MinimalAgent.

## Simple Tool Invocation

```python
from minimalagent import Agent, tool

@tool
def calculate(expression: str) -> dict:
    """Calculate the result of a mathematical expression.
    
    Args:
        expression: A mathematical expression as a string
        
    Returns:
        Dictionary with the result
    """
    try:
        # Be careful with eval in production code!
        result = eval(expression)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

# Initialize the agent
agent = Agent(tools=[calculate], show_reasoning=True)

# Run a calculation
response, reasoning = agent.run("What is 15 * 7 + 22?")

# Print the response
print(f"\nFinal response: {response}")
```

## Multiple Tools

```python
from minimalagent import Agent, tool
import random

@tool
def roll_dice(sides: int = 6, count: int = 1) -> dict:
    """Roll dice with the specified number of sides.
    
    Args:
        sides: Number of sides on each die
        count: Number of dice to roll
        
    Returns:
        Dictionary with the results
    """
    results = [random.randint(1, sides) for _ in range(count)]
    return {
        "results": results,
        "total": sum(results),
        "sides": sides,
        "count": count
    }

@tool
def flip_coin(count: int = 1) -> dict:
    """Flip a coin one or more times.
    
    Args:
        count: Number of coins to flip
        
    Returns:
        Dictionary with the results
    """
    results = [random.choice(["heads", "tails"]) for _ in range(count)]
    return {
        "results": results,
        "count": count,
        "heads": results.count("heads"),
        "tails": results.count("tails")
    }

# Initialize the agent with multiple tools
agent = Agent(tools=[roll_dice, flip_coin])

# Run a query that might use either tool
response, reasoning = agent.run("Roll 3 dice with 20 sides each")
print(f"Response: {response}")

# Run another query for the other tool
response, reasoning = agent.run("Flip 5 coins and tell me how many heads I got")
print(f"Response: {response}")
```

## Custom System Prompt

```python
from minimalagent import Agent, tool

@tool
def get_capital(country: str) -> dict:
    """Get the capital city of a country.
    
    Args:
        country: Name of the country
        
    Returns:
        Dictionary with country and capital
    """
    # In a real application, you would look this up in a database
    capitals = {
        "france": "Paris",
        "japan": "Tokyo",
        "australia": "Canberra",
        "brazil": "Brasília",
        "egypt": "Cairo"
    }
    
    country_lower = country.lower()
    if country_lower in capitals:
        return {"country": country, "capital": capitals[country_lower]}
    else:
        return {"country": country, "error": "Country not found in database"}

# Custom system prompt to guide the agent's behavior
system_prompt = """
You are a geography expert specializing in capital cities.
Always use formal language and provide brief educational facts about capitals when possible.
"""

# Initialize the agent with the custom system prompt
agent = Agent(
    tools=[get_capital],
    system_prompt=system_prompt
)

# Run a query
response, reasoning = agent.run("What is the capital of Japan?")
print(response)
```

## Error Handling

```python
from minimalagent import Agent, tool

@tool
def divide(a: float, b: float) -> dict:
    """Divide two numbers.
    
    Args:
        a: Numerator
        b: Denominator
        
    Returns:
        Dictionary with the result
    """
    try:
        if b == 0:
            return {"error": "Cannot divide by zero"}
        return {"result": a / b}
    except Exception as e:
        return {"error": str(e)}

# Initialize the agent
agent = Agent(tools=[divide])

# Run a valid query
response, reasoning = agent.run("What is 10 divided by 2?")
print(f"Valid division: {response}")

# Run a query that will trigger an error
response, reasoning = agent.run("What is 10 divided by 0?")
print(f"Division by zero: {response}")
```