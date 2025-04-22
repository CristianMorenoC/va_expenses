from typing import Dict, Any, List, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
import traceback
import sys
import json

from config import LLM_MODEL
from state.agent_state import AgentState
from tools.utils import tools
from agents.analyzer import IntentAnalyzer
from agents.retriever import ExpenseRetriever

# Initialize components
analyzer = IntentAnalyzer()
retriever = ExpenseRetriever()

# Debug information
print("Creating financial agent graph...")
print(f"Using LLM model: {LLM_MODEL}")
print(f"Available tools: {[t.name for t in tools]}")
sys.stdout.flush()

# Set up the model
llm = ChatAnthropic(model=LLM_MODEL)
llm_with_tools = llm.bind_tools(tools)

# System message for the assistant
SYSTEM_PROMPT = """You are an expert on personal finance and budgeting. 
You are given a user's financial data and you need to help them create a budget based on their income and expenses.

Using your tools, you can help users:
1. Add new expenses
2. Get summaries of their spending
3. Analyze spending trends
4. Create budget recommendations

Always be helpful, specific, and data-driven in your advice."""

sys_msg = SystemMessage(content=SYSTEM_PROMPT)

# Create a mapping of tool names to the actual tool functions
tool_map = {tool.name: tool for tool in tools}

# Define a custom tools condition function
def custom_tools_condition(state: AgentState) -> str:
    """
    Custom condition to determine whether to route to tools or end the conversation.
    
    Args:
        state: The current state
        
    Returns:
        "action" or "__end__" based on whether a tool call is detected
    """
    print("Checking if the assistant's response has a tool call...")
    
    try:
        messages = state["messages"]
        if not messages:
            print("No messages in state, ending.")
            return "__end__"
        
        last_message = messages[-1]
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            print("No tool_calls found, ending.")
            return "__end__"
        
        print(f"Found tool calls: {last_message.tool_calls}")
        return "action"
    except Exception as e:
        print(f"Error in custom_tools_condition: {str(e)}")
        traceback.print_exc()
        return "__end__"

# Define nodes
def analyze_intent(state: AgentState):
    """Analyze the user's intent from their message."""
    try:
        messages = state["messages"]
        user_message = messages[-1].content
        
        print(f"Analyzing intent: '{user_message}'")
        sys.stdout.flush()
        
        # Analyze the intent
        intent_data = analyzer.analyze(user_message, messages[:-1])
        
        print(f"Intent analysis result: {intent_data}")
        sys.stdout.flush()
        
        # Instead of returning a system message, add the intent information to the context
        # This avoids adding multiple system messages which causes errors with Claude
        context = state.get("context", {})
        context["intent"] = intent_data["intent"]
        context["confidence"] = intent_data["confidence"]
        
        if "extracted_data" in intent_data and intent_data["extracted_data"]:
            context["extracted_data"] = intent_data["extracted_data"]
        
        return {"context": context}
    except Exception as e:
        print(f"Error in analyze_intent: {str(e)}")
        traceback.print_exc()
        context = state.get("context", {})
        context["error"] = f"Intent analysis error: {str(e)}"
        return {"context": context}

def retrieve_data(state: AgentState):
    """Retrieve relevant financial data based on the user's intent."""
    try:
        context = state.get("context", {})
        
        # If there was an error in intent analysis, skip data retrieval
        if "error" in context:
            return {"context": context}
            
        intent = context.get("intent", "")
        
        print(f"Retrieving data for intent: {intent}")
        sys.stdout.flush()
        
        # Extract category from intent if available
        category = None
        if "extracted_data" in context and isinstance(context["extracted_data"], dict) and "category" in context["extracted_data"]:
            category = context["extracted_data"]["category"]
        
        # Determine what data to retrieve based on intent
        if "GET_SUMMARY" in intent or "ANALYZE_TREND" in intent:
            expense_data = retriever.get_expense_data(category=category, period="month")
            context["financial_data"] = {
                "expense_summary": expense_data
            }
            
            # Add budget comparison if relevant
            if "CREATE_BUDGET" in intent:
                budget_data = retriever.get_budget_comparison()
                if "error" not in budget_data:
                    context["financial_data"]["budget"] = budget_data
        
        return {"context": context}
    except Exception as e:
        print(f"Error in retrieve_data: {str(e)}")
        traceback.print_exc()
        context = state.get("context", {})
        context["error"] = f"Data retrieval error: {str(e)}"
        return {"context": context}

def assistant(state: AgentState):
    """Main assistant that processes messages and can use tools."""
    try:
        messages = state["messages"]
        context = state.get("context", {})
        
        print(f"Processing in assistant node with {len(messages)} messages")
        sys.stdout.flush()
        
        # Check for errors in previous steps
        if "error" in context:
            error_msg = context["error"]
            print(f"Error from previous step: {error_msg}")
            return {"messages": [AIMessage(content=f"I'm sorry, but I encountered an error: {error_msg}. Please try again or ask a different question.")]}
        
        # Create a complete message list with system message first
        complete_messages = [sys_msg]
        
        # Add a single internal system message with context if available
        if context:
            context_parts = []
            context_parts.append(f"User intent: {context.get('intent', 'UNKNOWN')} (confidence: {context.get('confidence', 0)})")
            
            if "extracted_data" in context:
                context_parts.append(f"Extracted data: {context['extracted_data']}")
            
            if "financial_data" in context:
                financial_data = context["financial_data"]
                if "expense_summary" in financial_data:
                    summary = financial_data["expense_summary"]
                    context_parts.append(f"Financial data retrieved: Total expenses: ${summary.get('total', 0):.2f} across {summary.get('count', 0)} expenses.")
                    
                    if "by_category" in summary and summary["by_category"]:
                        categories = ", ".join([f"{cat}: ${amt:.2f}" for cat, amt in summary["by_category"].items()])
                        context_parts.append(f"Expenses by category: {categories}")
                
                if "budget" in financial_data:
                    budget = financial_data["budget"]
                    context_parts.append(f"Budget comparison available. Current spending is ${budget.get('actual_total', 0):.2f} of ${budget.get('budget_total', 0):.2f} budgeted.")
            
            complete_messages.append(SystemMessage(content="\n".join(context_parts)))
        
        # Add user messages and any tool messages
        for msg in messages:
            if isinstance(msg, (HumanMessage, AIMessage, ToolMessage)):
                complete_messages.append(msg)
        
        # Print the message structure for debugging
        print(f"Message structure being sent to LLM:")
        for i, msg in enumerate(complete_messages):
            msg_type = type(msg).__name__
            msg_content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"  {i}: {msg_type} - {msg_content}")
        sys.stdout.flush()
        
        # Generate a response with the model that can use tools
        response = llm_with_tools.invoke(complete_messages)
        
        print(f"Response received from LLM: {type(response).__name__}")
        if hasattr(response, "tool_calls") and response.tool_calls:
            print(f"Tool calls detected: {response.tool_calls}")
        
        return {"messages": [response]}
    except Exception as e:
        print(f"Error in assistant node: {str(e)}")
        traceback.print_exc()
        return {"messages": [AIMessage(content=f"I apologize, but I encountered a technical error: {str(e)}. Please try again or contact support.")]}

def execute_tools(state: AgentState):
    """Execute tool calls and return the results."""
    try:
        messages = state["messages"]
        last_message = messages[-1]
        
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            print("No tool calls found in the message")
            return {"messages": messages}
        
        tool_calls = last_message.tool_calls
        print(f"Executing {len(tool_calls)} tool calls")
        
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})
            tool_id = tool_call.get("id")
            
            print(f"Executing tool: {tool_name} with args: {tool_args}")
            
            if tool_name in tool_map:
                try:
                    tool = tool_map[tool_name]
                    result = tool.invoke(tool_args)
                    print(f"Tool result: {result}")
                    
                    # Create a ToolMessage with the result
                    tool_message = ToolMessage(
                        content=str(result),
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    results.append(tool_message)
                except Exception as e:
                    error_msg = f"Error executing tool {tool_name}: {str(e)}"
                    print(error_msg)
                    traceback.print_exc()
                    
                    # Create a ToolMessage with the error
                    tool_message = ToolMessage(
                        content=f"Error: {error_msg}",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                    results.append(tool_message)
            else:
                error_msg = f"Tool {tool_name} not found"
                print(error_msg)
                
                # Create a ToolMessage with the error
                tool_message = ToolMessage(
                    content=f"Error: {error_msg}",
                    tool_call_id=tool_id,
                    name=tool_name
                )
                results.append(tool_message)
        
        # Return the updated messages with the tool results
        return {"messages": messages + results}
    except Exception as e:
        print(f"Error in execute_tools: {str(e)}")
        traceback.print_exc()
        return {"messages": messages + [AIMessage(content=f"Error executing tools: {str(e)}")]}

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