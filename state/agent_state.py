from typing import TypedDict, Annotated, Sequence, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState

# Define the state for the LangGraph
class AgentState(MessagesState):
    """
    Agent state for the financial advisor graph.
    
    Attributes:
        messages: Sequence of messages in the conversation (added to over time)
        context: Optional additional context for the agents (expenses data, budget info)
        user_info: Optional user information
    """
    pass  # MessagesState already includes the messages field with proper annotations

# If you need a more custom state definition, uncomment and modify this:
"""
class CustomAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    context: Dict[str, Any]  # Additional context like expense data
    user_info: Dict[str, Any]  # User information
""" 