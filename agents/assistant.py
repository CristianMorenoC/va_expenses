from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from state.agent_state import AgentState
import sys
import traceback
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from config import LLM_MODEL
from tools.utils import tools
from agents.analyzer import IntentAnalyzer
from agents.retriever import ExpenseRetriever

# Initialize components
analyzer = IntentAnalyzer()
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
