"""
Simple example showing how to use MinimalAgent.
"""

from minimalagent import Agent, tool


@tool(
    name="get_weather",
    description="Get weather information for a location",
    param_descriptions={"location": "The location to get weather for"},
)
def get_weather(location: str):
    """Get weather for a location.

    Args:
        location: The location to get weather for

    Returns:
        dict: Weather information
    """
    # Sample implementation (in a real app, this would call a weather API)
    weather_data = {
        "New York": {"temperature": 75, "condition": "sunny"},
        "San Francisco": {"temperature": 65, "condition": "foggy"},
        "Chicago": {"temperature": 80, "condition": "partly cloudy"},
    }

    # Return data for the requested location or a default response
    return {
        "temperature": weather_data.get(location, {"temperature": 70})["temperature"],
        "condition": weather_data.get(location, {"condition": "unknown"})["condition"],
        "location": location,
    }


if __name__ == "__main__":
    # Create agent with our weather tool
    agent = Agent(
        tools=[get_weather],
        show_reasoning=True,  # Show colorized reasoning display
        log_level="INFO",  # Show information and warning logs
        model_id="us.amazon.nova-pro-v1:0",  # Specified explicitly but using default value
        bedrock_region="us-west-2",  # Specified explicitly but using default value
        system_prompt="You are a helpful weather assistant. Respond with a friendly tone and focus on providing accurate weather information.",
    )

    # Run a query
    query = "What's the weather in San Francisco?"
    response = agent.run(query)

    # No need to print the response - it's printed by the agent when show_reasoning=True
