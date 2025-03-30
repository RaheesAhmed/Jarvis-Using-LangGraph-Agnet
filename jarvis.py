import getpass
import os
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from tools.web_search import search_on_web_tool
from tools.open_terminal import run_windows_command
from tools.ui_automation import click_coordinates, press_key
from tools.screen_reader import describe_screen_content
# Load the environment variables
load_dotenv()


# Initialize the model
model = ChatOpenAI(model="gpt-4o", temperature=0)

# Initialize the memory
memory = MemorySaver()

# For this tutorial we will use custom tool that returns pre-defined values for weather in two cities (NYC & SF)

@tool
def get_weather(city: Literal["nyc", "sf"]):
    """Use this to get weather information."""
    if city == "nyc":
        return "It might be cloudy in nyc"
    elif city == "sf":
        return "It's always sunny in sf"
    else:
        raise AssertionError("Unknown city")


# We can add our system prompt here
prompt = "You are Jarvis, the AI assistant created by Rahees Ahmed. You are a helpful assistant that can answer questions and help with tasks."

# Define the graph
tools = [get_weather, search_on_web_tool, run_windows_command, click_coordinates, describe_screen_content, press_key, describe_screen_content]

graph = create_react_agent(model, tools=tools, checkpointer=memory, prompt=prompt)

def run_agent_interaction(user_input: str, thread_id: str, graph):
    """
    Runs a single interaction with the LangGraph agent.

    Args:
        user_input: The input message from the user.
        thread_id: The conversation thread ID.
        graph: The compiled LangGraph agent.
        tools: The list of tools available to the agent.

    Returns:
        The final response content from the agent as a string, or an error message.
    """
    config = {"configurable": {"thread_id": thread_id}}
    inputs = {"messages": [HumanMessage(content=user_input)]}

    print(f"--- Running agent for input: '{user_input}' (Thread: {thread_id}) ---")

    # Stream until the interrupt
    stream_output = []
    print("Streaming initial agent response...")
    for chunk in graph.stream(inputs, config=config, stream_mode="values"):
         stream_output.append(chunk)
         # Optional: print intermediate steps here if desired
         message = chunk["messages"][-1]
         if not isinstance(message, tuple):
             print("Intermediate step:", type(message).__name__)
             # message.pretty_print() # Uncomment for full message details


    # Get state after the initial run/interrupt
    state = graph.get_state(config)
    print("State after initial stream:", state.next)

    last_message = state.values["messages"][-1]
    final_response_content = None

    # Check for tool calls
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print("Tool call detected.")
        # For simplicity, handling only the first tool call if multiple exist
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_id = tool_call["id"]

        print(f"Executing tool: {tool_name} with args: {tool_args} (ID: {tool_id})")

        tool_to_use = next((t for t in tools if t.name == tool_name), None)
        if tool_to_use:
            try:
                # Execute the tool
                result = tool_to_use.invoke(tool_args)
                print(f"Tool result: {result}")
                tool_message = ToolMessage(content=str(result), tool_call_id=tool_id)
            except Exception as e:
                print(f"Error executing tool {tool_name}: {e}")
                # Send error message back to the graph
                tool_message = ToolMessage(content=f"Error executing tool {tool_name}: {e}", tool_call_id=tool_id)

            # Update state with tool response/error
            graph.update_state(config, {"messages": [tool_message]})

            # Invoke the graph with None input to continue from the updated state
            print("\nInvoking graph to continue execution after tool call...")
            final_state = graph.invoke(None, config=config)

            # Extract the final AI message from the final state
            final_ai_message = final_state["messages"][-1]
            if isinstance(final_ai_message, AIMessage):
                 print("Final Agent Response:")
                 final_ai_message.pretty_print()
                 final_response_content = final_ai_message.content
            else:
                 print("Final state did not end with an AIMessage:", final_state)
                 final_response_content = "Agent did not produce a final AI response after tool call."

        else:
            print(f"Tool {tool_name} not found in the provided tool list.")
            final_response_content = f"Error: Tool {tool_name} not found."
            # It might be appropriate to update state with an error message here too
            # graph.update_state(config, {"messages": [ToolMessage(content=f"Tool {tool_name} not found.", tool_call_id=tool_id)]})
            # final_state = graph.invoke(None, config=config) # Or just return the error

    else:
        # No tool call, the answer should be in the last message of the current state or stream
        print("No tool call detected.")
        if isinstance(last_message, AIMessage):
            print("Final Agent Response:")
            last_message.pretty_print()
            final_response_content = last_message.content
        elif stream_output:
             # Check the very last message from the initial stream output
             final_message_in_stream = stream_output[-1]["messages"][-1]
             if isinstance(final_message_in_stream, AIMessage):
                 print("Final Agent Response (from stream end):")
                 final_message_in_stream.pretty_print()
                 final_response_content = final_message_in_stream.content
             else:
                print(f"No tool call and last message in state/stream ({type(final_message_in_stream).__name__}) is not AIMessage.")
                final_response_content = "Agent did not produce a final AI response."
        else:
             print("No tool call, no stream output, and last message in state is not AIMessage.")
             final_response_content = "Agent did not produce a final AI response."


    print(f"--- Agent interaction finished. Response: '{final_response_content}' ---")
    return final_response_content

# # Main execution block
# if __name__ == "__main__":
#     # Define a thread ID for the conversation
#     thread_id = "user_conversation_1"

#     # First interaction
#     response1 = run_agent_interaction("what is the weather in SF, CA?", thread_id, graph, tools)
#     print(f"\nInteraction 1 Response: {response1}")

#     # Second interaction (uses the same thread_id to maintain context)
#     response2 = run_agent_interaction("Who built you?", thread_id, graph, tools)
#     print(f"\nInteraction 2 Response: {response2}")
