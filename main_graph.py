from typing import Dict, Any
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

from config import LLM_MODEL
from state.agent_state import AgentState
from agents.analyzer import IntentAnalyzer
from agents.advisor import FinancialAdvisor
from agents.retriever import ExpenseRetriever
from tools.utils import tools

# Initialize agents
analyzer = IntentAnalyzer()
advisor = FinancialAdvisor()
retriever = ExpenseRetriever()

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

# Define nodes
def analyze_intent(state: AgentState):
    """Analyze the user's intent from their message."""
    messages = state["messages"]
    user_message = messages[-1].content
    
    # Analyze the intent
    intent_data = analyzer.analyze(user_message, messages[:-1])
    
    # Return as a system message to be added to the state
    intent_msg = SystemMessage(content=f"User intent: {intent_data['intent']} (confidence: {intent_data['confidence']})")
    
    # If we extracted specific data, include it
    if "extracted_data" in intent_data and intent_data["extracted_data"]:
        intent_msg.content += f"\nExtracted data: {intent_data['extracted_data']}"
    
    return {"messages": [intent_msg]}

def retrieve_data(state: AgentState):
    """Retrieve relevant financial data based on the user's query."""
    messages = state["messages"]
    
    # Find the intent message (should be the last system message)
    intent_msg = None
    for msg in reversed(messages):
        if isinstance(msg, SystemMessage) and "User intent:" in msg.content:
            intent_msg = msg
            break
    
    if not intent_msg:
        # No intent found, just provide general data
        expense_data = retriever.get_expense_data(period="month")
        data_msg = SystemMessage(content=f"Current month's financial data: Total expenses: ${expense_data['total']:.2f} across {expense_data['count']} expenses.")
        return {"messages": [data_msg]}
    
    # Extract category from intent if available
    category = None
    if "Extracted data:" in intent_msg.content and "category" in intent_msg.content:
        # Rough extraction - in production you'd want better parsing
        category_line = [line for line in intent_msg.content.split("\n") if "category" in line]
        if category_line:
            category = category_line[0].split("category")[1].strip(":' ,\"")
    
    # Determine what data to retrieve based on intent
    if "GET_SUMMARY" in intent_msg.content or "ANALYZE_TREND" in intent_msg.content:
        expense_data = retriever.get_expense_data(category=category, period="month")
        data_msg = SystemMessage(content=f"Financial data retrieved: Total expenses: ${expense_data['total']:.2f} across {expense_data['count']} expenses.")
        
        # Add budget comparison if relevant
        if "CREATE_BUDGET" in intent_msg.content:
            budget_data = retriever.get_budget_comparison()
            if "error" not in budget_data:
                data_msg.content += f"\nBudget comparison available. Current spending is ${budget_data['actual_total']:.2f} of ${budget_data['budget_total']:.2f} budgeted."
        
        return {"messages": [data_msg]}
    
    # Default minimal data context
    data_msg = SystemMessage(content="Context: User is asking about their finances.")
    return {"messages": [data_msg]}

def assistant(state: AgentState):
    """Main assistant that processes messages and can use tools."""
    messages = state["messages"]
    
    # Include the system message if it's not already there
    if not any(isinstance(msg, SystemMessage) and SYSTEM_PROMPT in msg.content for msg in messages):
        complete_messages = [sys_msg] + messages
    else:
        complete_messages = messages
    
    # Generate a response with the model that can use tools
    response = llm_with_tools.invoke(complete_messages)
    
    return {"messages": [response]}

# Define the graph
def create_agent_graph():
    """Create the financial advisor agent graph."""
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("intent_analyzer", analyze_intent)
    builder.add_node("data_retriever", retrieve_data)
    builder.add_node("assistant", assistant)
    builder.add_node("tools", ToolNode(tools))
    
    # Define the flow
    builder.add_edge(START, "intent_analyzer")
    builder.add_edge("intent_analyzer", "data_retriever")
    builder.add_edge("data_retriever", "assistant")
    
    # Conditional edge from assistant to either tools or end
    builder.add_conditional_edges(
        "assistant",
        tools_condition,
        {
            "action": "tools",
            "__end__": END
        }
    )
    
    # From tools back to assistant
    builder.add_edge("tools", "assistant")
    
    # Set up checkpointing for conversation memory
    memory = MemorySaver()
    
    # Compile the graph
    return builder.compile(checkpointer=memory)

# Create the agent graph
agent_graph = create_agent_graph()

# Export for use in console.py
def get_agent_graph():
    return agent_graph 