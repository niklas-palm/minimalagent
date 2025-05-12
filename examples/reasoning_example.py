"""
Example demonstrating MinimalAgent's reasoning persistence capabilities.

This example shows how to:
1. Enable reasoning persistence and real-time updates
2. Run the agent with a session ID
3. Access and analyze the reasoning data returned alongside the response
4. Retrieve reasoning data from DynamoDB later
5. Compare real-time vs. end-only reasoning updates
"""

import json
import time
import uuid

from minimalagent import Agent, tool


# Define a simple tool to count words in a text
@tool
def count_words(text: str) -> dict:
    """Count the number of words in a text.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with word count statistics
    """
    words = text.split()
    return {
        "word_count": len(words),
        "unique_words": len(set(words)),
        "average_word_length": sum(len(word) for word in words) / max(len(words), 1),
    }


@tool
def analyze_sentiment(text: str) -> dict:
    """Simple mock sentiment analysis.

    Args:
        text: Text to analyze

    Returns:
        Dictionary with sentiment analysis results
    """
    # This is a mock implementation - in a real application, you'd use a proper
    # sentiment analysis library or service
    positive_words = ["good", "great", "excellent", "wonderful", "happy"]
    negative_words = ["bad", "terrible", "awful", "horrible", "sad"]

    words = text.lower().split()
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)

    # Simple sentiment score calculation
    total = positive_count + negative_count
    if total > 0:
        sentiment_score = (positive_count - negative_count) / total
    else:
        sentiment_score = 0

    return {
        "sentiment_score": sentiment_score,
        "positive_words": positive_count,
        "negative_words": negative_count,
        "is_positive": sentiment_score > 0,
        "is_negative": sentiment_score < 0,
        "is_neutral": sentiment_score == 0,
    }


def display_reasoning_data(reasoning, title="Reasoning Data"):
    """Helper function to display reasoning in a formatted way."""
    print(f"\n{title}:")
    print(f"  • Query: {reasoning.get('query', 'N/A')}")
    print(f"  • Total steps: {reasoning.get('total_steps', 0)}")

    # Show each step's thinking
    for i, step in enumerate(reasoning.get("steps", [])):
        print(f"\n  Step {i+1} thinking:")
        # Truncate long content for display
        thinking = step.get("thinking", "")
        if thinking:
            print(f"    {thinking[:150]}{'...' if len(thinking) > 150 else ''}")

        # Show tools used in this step
        tools = step.get("tools", [])
        if tools:
            print(f"\n    Tools used:")
            for tool in tools:
                print(f"    • {tool['name']}")
                print(f"      Inputs: {tool['inputs']}")
                if "result" in tool and "content" in tool["result"]:
                    content = tool["result"]["content"][0]
                    if "json" in content:
                        print(f"      Result: {json.dumps(content['json'], indent=2)}")

    # Show final thinking if available
    if "final_thinking" in reasoning:
        print("\n  Final reasoning:")
        final_thinking = reasoning["final_thinking"]
        print(f"    {final_thinking[:150]}{'...' if len(final_thinking) > 150 else ''}")


def run_example_with_realtime_reasoning():
    """Run agent with real-time reasoning updates."""
    print("\n===== REAL-TIME REASONING EXAMPLE =====")

    # Create a unique session ID
    session_id = f"realtime-{uuid.uuid4()}"[:20]
    print(f"Using session ID: {session_id}")

    # Create the agent with real-time reasoning enabled
    agent = Agent(
        tools=[count_words, analyze_sentiment],
        use_session_memory=True,  # Required for real-time reasoning
        real_time_reasoning=True,  # Enable real-time updates
        show_reasoning=True,  # Show reasoning in console
    )

    # Run the agent with a query that will use both tools
    print("\nRunning agent with real-time reasoning updates...")
    query = "Analyze this text: The quick brown fox jumps over the lazy dog. It was a good day for everyone!"

    # Execute the query
    response, reasoning = agent.run(query, session_id=session_id)

    # Display the response
    print("\nAgent response:")
    print(response)

    # Display reasoning from the returned object
    display_reasoning_data(reasoning, "Reasoning returned by run() method")

    # Wait a moment to ensure data is saved
    time.sleep(1)

    # Retrieve reasoning from DynamoDB
    retrieved_reasoning = agent.get_reasoning(session_id)
    print("\nSuccessfully retrieved reasoning from DynamoDB")

    return session_id


def run_example_without_realtime_reasoning():
    """Run agent without real-time reasoning updates."""
    print("\n===== END-ONLY REASONING EXAMPLE =====")

    # Create a unique session ID
    session_id = f"end-only-{uuid.uuid4()}"[:20]
    print(f"Using session ID: {session_id}")

    # Create the agent with real-time reasoning disabled
    agent = Agent(
        tools=[count_words, analyze_sentiment],
        use_session_memory=True,  # Enable session storage
        real_time_reasoning=False,  # Disable real-time updates
        show_reasoning=True,  # Show reasoning in console
    )

    # Run the agent with the same query
    print("\nRunning agent without real-time reasoning updates...")
    query = "Analyze this text: The quick brown fox jumps over the lazy dog. It was a good day for everyone!"

    # Execute the query
    response, reasoning = agent.run(query, session_id=session_id)

    # Display the response
    print("\nAgent response:")
    print(response)

    # Display reasoning from the returned object
    display_reasoning_data(reasoning, "Reasoning returned by run() method")

    # Wait a moment to ensure data is saved
    time.sleep(1)

    # Retrieve reasoning from DynamoDB
    retrieved_reasoning = agent.get_reasoning(session_id)
    print("\nSuccessfully retrieved reasoning from DynamoDB")

    return session_id


def run_reasoning_history_example(session_id):
    """Demonstrate retrieving full reasoning history."""
    print("\n===== REASONING HISTORY EXAMPLE =====")

    # Create agent with the same tools to retrieve history
    agent = Agent(
        tools=[count_words, analyze_sentiment],  # Need to include tools
        use_session_memory=True,
        show_reasoning=False,  # No need to show output for this example
    )

    # Add a second interaction to the same session
    print(f"\nAdding a second interaction to session {session_id}...")
    second_query = "What is the sentiment of 'This was a terrible experience'?"

    # Run a second query with the same session ID
    response, _ = agent.run(second_query, session_id=session_id)

    print(f"Response to second query: {response}")

    # Wait a moment to ensure data is saved
    time.sleep(1)

    # Retrieve full reasoning history
    print("\nRetrieving full reasoning history...")
    reasoning_history = agent.get_reasoning_history(session_id)

    # Display summary of history
    print(f"\nFound {len(reasoning_history)} reasoning entries:")
    for i, entry in enumerate(reasoning_history):
        print(f"\n{i+1}. Query: {entry.get('query', 'N/A')}")
        print(f"   Total steps: {entry.get('total_steps', 0)}")
        print(
            f"   Final response snippet: {entry.get('final_response', 'N/A')[:50]}..."
        )


if __name__ == "__main__":
    # Run example with real-time updates
    realtime_session_id = run_example_with_realtime_reasoning()

    # Run example without real-time updates
    end_only_session_id = run_example_without_realtime_reasoning()

    # Demonstrate reasoning history with multiple interactions
    run_reasoning_history_example(realtime_session_id)

    print("\nExample complete!")
    print("Key points demonstrated:")
    print("1. Real-time reasoning updates - reasoning data is saved during execution")
    print("2. End-only reasoning updates - reasoning data is saved only at the end")
    print(
        "3. Reasoning history - retrieving multiple interactions for the same session"
    )
