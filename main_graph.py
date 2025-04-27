from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
import traceback
import sys

from state.agent_state import AgentState
from agents.assistant import assistant
from tools.nodes.assistant.assistant_nodes import custom_tools_condition
from tools.nodes.assistant.assistant_nodes import analyze_intent, retrieve_data, execute_tools

# Define the graph
def create_agent_graph():
    """Create the financial advisor agent graph."""
    try:
        print("Creating StateGraph...")
        builder = StateGraph(AgentState)
        
        print("Adding nodes to graph...")
        # Add nodes
        builder.add_node("intent_analyzer", analyze_intent)
        builder.add_node("data_retriever", retrieve_data)
        builder.add_node("assistant", assistant)
        builder.add_node("action", execute_tools)  # Custom tool execution node
        
        print("Defining graph edges...")
        # Define the flow
        builder.add_edge(START, "intent_analyzer")
        builder.add_edge("intent_analyzer", "data_retriever")
        builder.add_edge("data_retriever", "assistant")
        
        # Conditional edge from assistant to either tools or end
        print("Adding conditional edges...")
        builder.add_conditional_edges(
            "assistant",
            custom_tools_condition,
            {
                "action": "action",
                "__end__": END
            }
        )
        
        # From tools back to assistant
        builder.add_edge("action", "assistant")
        
        # Set up checkpointing for conversation memory
        print("Setting up memory...")
        memory = MemorySaver()
        
        # Compile the graph
        print("Compiling graph...")
        compiled_graph = builder.compile(checkpointer=memory)
        print("Graph compiled successfully")
        sys.stdout.flush()
        
        return compiled_graph
    except Exception as e:
        print(f"Error creating agent graph: {str(e)}")
        traceback.print_exc()
        raise

# Create the agent graph
print("Initializing agent graph...")
try:
    agent_graph = create_agent_graph()
    print("Agent graph created successfully!")
except Exception as e:
    print(f"Failed to create agent graph: {str(e)}")
    traceback.print_exc()
    # Create a minimal fallback graph
    agent_graph = None

# Export for use in console.py
def get_agent_graph():
    if agent_graph is None:
        raise RuntimeError("Agent graph could not be initialized")
    return agent_graph 