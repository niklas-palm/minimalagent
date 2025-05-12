"""
Example showing how to use MinimalAgent with docstring-based tools.
"""

from minimalagent import Agent, tool


@tool  # Simple usage - extracts everything from docstring
def get_weather(location: str, units: str = "metric") -> dict:
    """Get current weather information for a specified location.

    Retrieves real-time weather data including temperature and
    conditions for the requested location.

    Args:
        location: City name or geographic coordinates to get weather for
        units: Measurement system to use (metric or imperial)

    Returns:
        Dict containing weather information
    """
    # Sample implementation (in a real app, this would call a weather API)
    weather_data = {
        "New York": {"temperature": 75, "condition": "sunny"},
        "San Francisco": {"temperature": 65, "condition": "foggy"},
        "Seattle": {"temperature": 55, "condition": "rainy"},
    }

    # Return data for the requested location or a default response
    result = {
        "temperature": weather_data.get(location, {"temperature": 70})["temperature"],
        "condition": weather_data.get(location, {"condition": "unknown"})["condition"],
        "location": location,
        "units": units,
    }

    # Convert to imperial if requested
    if units.lower() == "imperial" and "temperature" in result:
        result["temperature"] = round(result["temperature"] * 9 / 5 + 32)

    return result


@tool
def search_database(query: str, limit: int = 10) -> list:
    """Search the database for records matching the query.

    Args:
        query: The search term to look for in the database
        limit: Maximum number of results to return

    Returns:
        List of matching records
    """
    # Sample implementation (in a real app, this would query a database)
    database = [
        {"id": 1, "name": "Apple", "category": "Fruit"},
        {"id": 2, "name": "Banana", "category": "Fruit"},
        {"id": 3, "name": "Carrot", "category": "Vegetable"},
        {"id": 4, "name": "Dill", "category": "Herb"},
        {"id": 5, "name": "Eggplant", "category": "Vegetable"},
    ]

    # Simple search implementation
    results = []
    for item in database:
        if (
            query.lower() in item["name"].lower()
            or query.lower() in item["category"].lower()
        ):
            results.append(item)
            if len(results) >= limit:
                break

    return results


# Example with overridden properties but still using docstring for other info
@tool(
    name="calculator",  # Override the name
    description="Performs basic arithmetic operations",  # Override the description
)
def math_operation(operation: str, number1: float, number2: float = 0) -> dict:
    """Calculate result of arithmetic operation between two numbers.

    Args:
        operation: The operation to perform (add, subtract, multiply, divide)
        number1: First number in the operation
        number2: Second number in the operation

    Returns:
        Dict with operation, inputs, and result
    """
    result = None

    if operation.lower() == "add":
        result = number1 + number2
    elif operation.lower() == "subtract":
        result = number1 - number2
    elif operation.lower() == "multiply":
        result = number1 * number2
    elif operation.lower() == "divide":
        if number2 == 0:
            raise ValueError("Cannot divide by zero")
        result = number1 / number2
    else:
        raise ValueError(f"Unsupported operation: {operation}")

    return {
        "operation": operation,
        "number1": number1,
        "number2": number2,
        "result": result,
    }


if __name__ == "__main__":
    # Create agent with our tools
    agent = Agent(
        tools=[get_weather, search_database, math_operation],
        show_reasoning=True,  # Show colorized reasoning display
        log_level="WARNING",  # Only show warnings and errors (default)
    )

    # Run a weather query
    print("\n--- Weather Query ---")
    agent.run("What's the weather in Seattle and what would that be in Fahrenheit?")

    # Run a database search
    print("\n--- Database Query ---")
    agent.run("Find fruits in the database")

    # Run a calculation
    print("\n--- Math Query ---")
    agent.run("Use the calculator to divide 24.5 by 3.5")
