import os
import asyncio
from typing import Dict, Any
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


from agents import set_tracing_export_api_key

set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))

# Define tools using the function_tool decorator
@function_tool
async def fetch_weather(location: str) -> str:
    """Fetch the current weather for a location.
    
    Args:
        location: The city and state, e.g. "San Francisco, CA"
    
    Returns:
        A string containing the weather forecast.
    """
    # In a real app, this would call a weather API
    return f"It's sunny and 72°F in {location}."

@function_tool
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression.
    
    Args:
        expression: A mathematical expression as a string, e.g. "2 + 2"
    
    Returns:
        The result of the calculation.
    """
    try:
        # Restrict eval to safe operations
        allowed_names = {"abs": abs, "round": round, "min": min, "max": max}
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return f"The result of {expression} is {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"

@function_tool
async def search_web(query: str) -> Dict[str, Any]:
    """Search the web for information about a query.
    
    Args:
        query: The search query string
    
    Returns:
        A dictionary containing search results.
    """
    # Simulated search results
    results = {
        "python": "Python is a high-level, interpreted programming language known for its readability.",
        "openai": "OpenAI is an AI research laboratory consisting of the for-profit corporation OpenAI LP and its parent company.",
        "agents": "In the context of AI, agents are systems that can perceive their environment and take actions to achieve goals.",
        "weather": "Weather refers to the state of the atmosphere, including temperature, humidity, precipitation, wind, and clouds."
    }

    # Default response for unknown queries
    default_response = "I couldn't find specific information about that. Try another search query."

    # Simple keyword matching
    for keyword, result in results.items():
        if keyword.lower() in query.lower():
            return {
                "query": query,
                "results": [
                    {"title": f"About {keyword.capitalize()}", "content": result}
                ]
            }

    return {
        "query": query,
        "results": [
            {"title": "No specific results", "content": default_response}
        ]
    }

@function_tool
async def recommend_restaurant(cuisine: str, location: str) -> str:
    """Find top restaurant recommendations.
    
    Args:
        cuisine: Type of food desired (e.g., Italian, Thai, etc.)
        location: City or neighborhood for dining
    
    Returns:
        A string with restaurant recommendations.
    """
    # Simulated restaurant recommendations
    restaurants = {
        "italian": {
            "san francisco": "Bella Trattoria - 4.5 stars, authentic Italian cuisine",
            "new york": "Carbone - 4.7 stars, upscale Italian dining",
            "chicago": "Spiaggia - 4.6 stars, classic Italian dishes"
        },
        "thai": {
            "san francisco": "Kin Khao - 4.4 stars, traditional Thai food",
            "new york": "SriPraPhai - 4.5 stars, acclaimed Thai restaurant",
            "chicago": "Arun's Thai - 4.8 stars, fine Thai dining"
        },
        "mexican": {
            "san francisco": "La Taqueria - 4.6 stars, famous for burritos",
            "new york": "Cosme - 4.5 stars, upscale Mexican cuisine",
            "chicago": "Frontera Grill - 4.7 stars, authentic Mexican dishes"
        }
    }

    cuisine = cuisine.lower()
    location = location.lower()

    if cuisine in restaurants and location in restaurants[cuisine]:
        return restaurants[cuisine][location]
    else:
        return f"I couldn't find {cuisine} restaurant recommendations for {location}."

async def main():
    # Create the travel assistant agent with tools
    travel_assistant = Agent(
        name="Travel Assistant",
        instructions="""You are a helpful travel assistant that can provide weather information
        and restaurant recommendations to users planning trips.
        
        Use the fetch_weather tool to check weather conditions for a location.
        Use the recommend_restaurant tool to suggest dining options based on cuisine and location.
        Use the search_web tool to find general information about travel destinations.
        Use the calculate tool for any trip-related calculations (currency conversion, distances, etc.)
        
        Be friendly, helpful, and concise in your responses.""",
        tools=[fetch_weather, recommend_restaurant, search_web, calculate]
    )

    print("Travel Assistant Agent")
    print("Type 'exit' to quit")

    # Interactive loop for conversation
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break

        # Run the agent with user input
        result = await Runner.run(travel_assistant, user_input)
        print(f"\nAssistant: {result.final_output}")

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY in the .env file")
        exit(1)

    # Run the async main function
    asyncio.run(main())