import os
import asyncio
from typing import Dict, Any
from agents import Agent, Runner, function_tool
from dotenv import load_dotenv
import requests
import inspect
import asyncio
import os  # You're using os.getenv

from typing import Callable, Coroutine, Any  # For type hinting

# Load environment variables
load_dotenv()
from agents import set_tracing_export_api_key
set_tracing_export_api_key(os.getenv("OPENAI_API_KEY"))


TOOL_CONFIGS = {
    "get_facts_about_cats": {
        "kwargs": [],
        "url": "https://catfact.ninja/fact",
        "description": "Get a fun fact about cats!",
        "response":[{"name": "fact", "description": "A fun fact about cats"}, {"name": "length", "description": "The length of the fact"}]
    },
    "get_details_of_a_person": {
        "kwargs": [{"name": "name", "description": "The name of the person"}],
        "description": "Get the name, age and count of a person!",
        "url": "https://api.agify.io/",
        "serviceId": "1",
        "operationId": "uuid2",
        "method": "GET",
        "response":[{"name": "name", "description": "The name of the person"}, 
                    {"name": "age", "description": "The predicted age for the name"},
                    {"name":"count", "description": "Number of records found with this name"}]
    },
    "get_country_details": {
        "kwargs": [{"name": "name", "description": "The name of the person"}],
        "description": "Get the name, age and country of a person!",
        "url": "https://api.nationalize.io/",
        "method": "GET",
        "response":[{"name": "name", "description": "The name of the person"}, 
                    {"name": "country", "description": "The predicted age for the name"},
                    {"name":"count", "description": "Number of records found with this name"}]
    }
}
    
def get_tool_description(tool_id: str, required_args: list, response_parameters: list) -> str:
    """
    Generate a description for a specific tool based on its configuration.
    
    Args:
        tool_id: The identifier for the tool.
        required_args: List of required arguments for the tool.
        response_parameters: List of parameters returned by the tool.
        
    Returns:
        A string description of the tool.
    """
    # Get tool configuration
    tool_config = TOOL_CONFIGS.get(tool_id, {})
    
    # Get description from config or generate from tool ID
    base_description = tool_config.get("description", tool_id.replace('_', ' ').capitalize())
    
    # Build description
    description = f"""
    {base_description}
    """
    
    # Add arguments section if there are required args
    if required_args:
        description += """
    Args:
    """
        for arg_detail in required_args:
            if isinstance(arg_detail, dict):
                arg_name = arg_detail.get("name", "")
                arg_desc = arg_detail.get("description", f"The {arg_name} parameter")
                description += f"    {arg_name}: {arg_desc}\n    "
    
    # Add returns section
    if response_parameters:
        description += """
    Returns:
    """
        for param in response_parameters:
            if isinstance(param, dict):
                param_name = param.get("name", "")
                param_desc = param.get("description", "")
                description += f"    {param_name}: {param_desc}\n    "
    
    return description

def create_tool(tool_id: str, tool_config: dict) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    Creates an asynchronous tool function with a generated description.

    Args:
        tool_config: Dictionary containing tool configurations.

    Returns:
        An asynchronous function representing the tool.
    """
    required_args = tool_config.get("kwargs", [])
    url_template = tool_config.get("url", "")
    response_parameters = tool_config.get("response", [])
    
    async def tool_function(*args: Any, **kwargs: Any) -> Any:
        try:
            # Build URL with query parameters
            url = url_template
            
            # Handle positional arguments
            if args and required_args:
                for i, arg_details in enumerate(required_args):
                    if i < len(args) and isinstance(arg_details, dict):
                        # Add parameter to URL
                        arg_name = arg_details.get("name", "")
                        if arg_name:
                            param_separator = '?' if '?' not in url else '&'
                            url = f"{url}{param_separator}{arg_name}={args[i]}"
            
            # Handle keyword arguments
            for key, value in kwargs.items():
                # Check if this key is in the required arguments
                for arg_detail in required_args:
                    if isinstance(arg_detail, dict) and arg_detail.get("name") == key:
                        # Add parameter to URL
                        param_separator = '?' if '?' not in url else '&'
                        url = f"{url}{param_separator}{key}={value}"
                        break
            
            response = requests.get(url, verify=False)
            
            # Parse JSON response
            json_data = response.json()
            return json_data
        except Exception as e:
            return f"Error calling API: {str(e)}"
    
    tool_function.__doc__ = get_tool_description(tool_id, required_args, response_parameters)
    tool_function.__name__ = tool_id
    
    return tool_function


async def main():
    
    # Create the tools based on configuration
    tool_list: list[Callable[..., Coroutine[Any, Any, Any]]] = []
    for tool_name, tools_details in TOOL_CONFIGS.items():
        tool = create_tool(tool_name, tools_details)
        tool_list.append(tool)

    # Assuming 'Agent' and 'Runner' are defined elsewhere in your code
    # and that they can handle asynchronous functions.
    class Agent:  # Placeholder for your Agent class
        def __init__(self, name: str, instructions: str, tools: list[Callable[..., Coroutine[Any, Any, Any]]]):
            self.name = name
            self.instructions = instructions
            self.tools = tools

    class Runner:  # Placeholder for your Runner class
        @staticmethod
        async def run(agent: Agent, user_input: str) -> Any:
            # Simulate running the agent and tools
            print(f"Agent '{agent.name}' received input: '{user_input}'")
            print("Available tools:")
            for tool in agent.tools:
                print(f"- {tool.__name__}: {tool.__doc__}")  # Access name and docstring

            # Process user query
            user_input_lower = user_input.lower()
            
            # Determine which tools might be relevant based on user input
            relevant_tools = []
            for tool in agent.tools:
                # Check for keywords in tool name
                keywords = tool.__name__.split('_')
                if any(keyword in user_input_lower for keyword in keywords):
                    relevant_tools.append(tool)

            # If multiple tools are relevant, run them all and combine results
            if len(relevant_tools) > 1:
                # Extract parameters once
                name_param = Runner._extract_parameter(user_input, "name")
                
                # Run all relevant tools with the same parameters
                combined_result = {}
                
                # Execute all relevant tools
                for tool in relevant_tools:
                    tool_config = TOOL_CONFIGS.get(tool.__name__, {})
                    params = {}
                    
                    # Build parameters for this tool
                    for arg_detail in tool_config.get("kwargs", []):
                        if isinstance(arg_detail, dict):
                            arg_name = arg_detail.get("name", "")
                            if arg_name:
                                params[arg_name] = Runner._extract_parameter(user_input, arg_name)
                    
                    # Execute the tool
                    result = await tool(**params)
                    
                    # Merge results, avoiding duplicate keys
                    if isinstance(result, dict):
                        for key, value in result.items():
                            if key not in combined_result:
                                combined_result[key] = value
                
                return type('Result', (object,), {"final_output": combined_result})
            
            # If only one tool is relevant, use it
            elif len(relevant_tools) == 1:
                tool = relevant_tools[0]
                tool_config = TOOL_CONFIGS.get(tool.__name__, {})
                params = {}
                
                # Extract parameters for this tool
                for arg_detail in tool_config.get("kwargs", []):
                    if isinstance(arg_detail, dict):
                        arg_name = arg_detail.get("name", "")
                        if arg_name:
                            params[arg_name] = Runner._extract_parameter(user_input, arg_name)
                
                # Execute the tool
                result = await tool(**params)
                return type('Result', (object,), {"final_output": result})
            
            # No relevant tools found, try all tools
            else:
                # Extract common parameters
                name_param = Runner._extract_parameter(user_input, "name")
                
                # Try all tools with extracted parameters and merge results
                combined_result = {}
                
                for tool in agent.tools:
                    tool_config = TOOL_CONFIGS.get(tool.__name__, {})
                    params = {}
                    
                    # Build parameters for this tool
                    for arg_detail in tool_config.get("kwargs", []):
                        if isinstance(arg_detail, dict):
                            arg_name = arg_detail.get("name", "")
                            if arg_name:
                                params[arg_name] = Runner._extract_parameter(user_input, arg_name)
                    
                    try:
                        # Execute the tool
                        result = await tool(**params)
                        
                        # Merge results, avoiding duplicate keys
                        if isinstance(result, dict):
                            for key, value in result.items():
                                if key not in combined_result:
                                    combined_result[key] = value
                    except Exception:
                        # Skip tools that fail
                        continue
                
                if combined_result:
                    return type('Result', (object,), {"final_output": combined_result})
                
                # Default response if no results were generated
                return type('Result', (object,), {"final_output": "I'm not sure what information you're looking for. You can ask for cat facts or age predictions."})
        
        @staticmethod
        def _extract_parameter(input_text: str, param_name: str) -> str:
            """Extract a parameter value from user input text.
            
            Args:
                input_text: The user input text
                param_name: The name of the parameter to extract
                
            Returns:
                The extracted parameter value or a default value
            """
            parts = input_text.lower().split()
            
            # For "name" parameter specifically
            if param_name == "name":
                # Look for phrases like "age of John" or "details for Sarah"
                for i, part in enumerate(parts):
                    if part in ["of", "for", "about"] and i+1 < len(parts):
                        return parts[i+1]
                    
                # Look for patterns like "name is John" or "for name John"
                for i, part in enumerate(parts):
                    if part == param_name and i+2 < len(parts) and parts[i+1] in ["is", "of", "for"]:
                        return parts[i+2]
                    if part in ["for", "about", "with"] and i+1 < len(parts) and parts[i+1] == param_name and i+2 < len(parts):
                        return parts[i+2]
            
            # Default values for known parameters
            defaults = {
                "name": "meelad"
            }
            
            return defaults.get(param_name, "")

    assistant = Agent(
        name="Multi-Tool Assistant",
        instructions="""You are a helpful assistant that can provide information about cats and predict ages based on names.
        Use the available function tools to give accurate information required.
        Be friendly, helpful, and concise in your responses.""",
        tools=tool_list
    )

    print("Multi-Tool Assistant")
    print("Type 'exit' to quit")

    # Interactive loop for conversation
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break

        # Run the agent with user input
        result = await Runner.run(assistant, user_input)
        
        # Format the response nicely
        if isinstance(result.final_output, dict):
            # if "fact" in result.final_output:
            #     # Cat facts response
            #     formatted_output = f"{result.final_output['fact']}"
            # elif "age" in result.final_output:
            #     # Age prediction response
            #     formatted_output = f"Age for '{result.final_output['name']}': {result.final_output['age']} years old (based on {result.final_output['count']} records)"
            # else:
            #     # Generic dictionary response
                formatted_output = ", ".join([f"{k}: {v}" for k, v in result.final_output.items()])
        else:
            # String or other response
            formatted_output = result.final_output
            
        print(f"\nAssistant: {formatted_output}")


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("Please set your OPENAI_API_KEY in the .env file")
        exit(1)

    # Run the async main function
    asyncio.run(main())