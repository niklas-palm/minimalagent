"""
Example showing how to use MinimalAgent with session persistence.
"""

from minimalagent import Agent, tool


@tool(
    name="get_weather",
    description="Get weather information for a location and date",
    param_descriptions={
        "location": "The location to get weather for",
        "date": "The date to get weather for (today, tomorrow, etc)",
    },
)
def get_weather(location: str, date: str = "today"):
    """Get weather for a location and date.

    Args:
        location: The location to get weather for
        date: The date to get weather for (today, tomorrow, etc)

    Returns:
        dict: Weather information
    """
    # Sample implementation (in a real app, this would call a weather API)
    weather_data = {
        "today": {
            "New York": {"temperature": 75, "condition": "sunny"},
            "San Francisco": {"temperature": 65, "condition": "foggy"},
            "Seattle": {"temperature": 55, "condition": "rainy"},
        },
        "tomorrow": {
            "New York": {"temperature": 72, "condition": "partly cloudy"},
            "San Francisco": {"temperature": 67, "condition": "cloudy"},
            "Seattle": {"temperature": 58, "condition": "showers"},
        },
    }

    day_data = weather_data.get(date.lower(), weather_data["today"])

    # Return data for the requested location or a default response
    return {
        "temperature": day_data.get(location, {"temperature": 70})["temperature"],
        "condition": day_data.get(location, {"condition": "unknown"})["condition"],
        "location": location,
        "date": date,
    }


if __name__ == "__main__":
    # Create agent with session support (implied opt-in by providing table name)
    agent = Agent(
        tools=[get_weather],
        show_reasoning=True,  # Show agent's reasoning process
        model_id="us.amazon.nova-pro-v1:0",
        bedrock_region="us-west-2",          # Region for Amazon Bedrock
        memory_region="us-west-2",           # Optional: can be different from bedrock_region
        session_table_name="weather-agent-sessions",  # Custom table name (also enables session memory)
        session_ttl=7200,  # 2 hours session TTL
    )

    # Generate a session ID (in a real app, this might be tied to a user)
    # Using a simpler format than UUID for session_id validation
    import random
    import string
    
    # Generate a random string of letters and numbers (valid session ID format)
    session_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    print(f"Starting new conversation with session ID: {session_id}")

    # First query - this will start a new session
    query1 = "What's the weather in Seattle?"
    print(f"\nQUERY 1: {query1}")
    agent.run(query1, session_id=session_id)

    # Second query - this will continue the same session with memory of previous interaction
    query2 = "How about tomorrow?"
    print(f"\nQUERY 2: {query2}")
    agent.run(query2, session_id=session_id)

    # Third query - testing additional context
    query3 = "And what about in San Francisco?"
    print(f"\nQUERY 3: {query3}")
    agent.run(query3, session_id=session_id)

    print("\nSession demonstration complete!")
