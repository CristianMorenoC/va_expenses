import os
from typing import TypedDict, Annotated, Sequence
from dotenv import load_dotenv

import uuid
from main_graph import get_agent_graph
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage, HumanMessage, FunctionMessage, SystemMessage
from langgraph.graph import StateGraph, END, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from tools.utils import tools
from console import clear_screen, display_header, display_help, format_message


# Load environment variables from .env file
load_dotenv()

# Debug info
print(f"Loaded .env file, current directory: {os.getcwd()}")
print(f"ANTHROPIC_API_KEY present: {'Yes' if os.getenv('ANTHROPIC_API_KEY') else 'No'}")

# Retrieve API keys with fallbacks
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("Warning: ANTHROPIC_API_KEY not found in environment variables")
    # You could set a default key for development or testing here
    # ANTHROPIC_API_KEY = "your-default-key-for-testing"
else:
    # Set the API key in the environment for the library to use
    os.environ["ANTHROPIC_API_KEY"] = ANTHROPIC_API_KEY
    print("Successfully loaded ANTHROPIC_API_KEY from environment")


llm = ChatAnthropic(model="claude-3-5-haiku-latest")
llm_with_tools = llm.bind_tools(tools)


# System message
sys_msg = SystemMessage(content="You are an expert on personal finance and budgeting. You are given a user's financial data and you need to help them create a budget based on their income and expenses.")

# Node
def assistant(state: MessagesState):
   return {"messages": [llm_with_tools.invoke([sys_msg] + state["messages"])]}

builder = StateGraph(MessagesState)

builder.add_node("assistant", assistant)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition
)
builder.add_edge("tools", "assistant")
memory = MemorySaver()

app = builder.compile(checkpointer=memory)

# === CONSOLE LOOP ===
def main():
    """Main function for the console interface."""
    clear_screen()
    display_header()
    
    agent = get_agent_graph()
    session_id = str(uuid.uuid4())
    
    while True:
        try:
            user_input = input(colorize("\nYou: ", "36;1"))
            
            if user_input.lower() in ("exit", "quit"):
                print(colorize("\nThank you for using VA Expenses. Goodbye!", "33;1"))
                break
                
            if user_input.lower() == "help":
                display_help()
                continue
                
            if user_input.lower() == "clear":
                clear_screen()
                display_header()
                continue
            
            if not user_input.strip():
                continue
            
            # Set up the conversation configuration with the session ID
            config = {"configurable": {"thread_id": session_id}}
            
            # Create initial state with the user message
            state = {"messages": [HumanMessage(content=user_input)]}
            
            # Get the response from the agent
            result = agent.invoke(state, config)
            
            # Print the assistant's response, skipping system messages
            for msg in result["messages"]:
                if hasattr(msg, 'type') and msg.type in ('ai', 'human'):
                    print(format_message(msg))
        
        except KeyboardInterrupt:
            print(colorize("\n\nInterrupted by user. Exiting...", "31;1"))  # Red
            break
        except Exception as e:
            print(colorize(f"\nAn error occurred: {str(e)}", "31;1"))  # Red
    
if __name__ == "__main__":
    main() 