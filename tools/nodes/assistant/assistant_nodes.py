from langchain_core.messages import AIMessage, ToolMessage
import traceback
import sys

from state.agent_state import AgentState
from tools.utils import tools
from agents.analyzer import IntentAnalyzer
from agents.retriever import ExpenseRetriever

# Initialize components
analyzer = IntentAnalyzer()
retriever = ExpenseRetriever()


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
