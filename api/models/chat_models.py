from pydantic import BaseModel, Field
from typing import List, Optional

class Message(BaseModel):
    """Model for chat messages in the conversation."""
    role: str = Field(..., description="Role of the message sender (user, assistant, tool)")
    content: str = Field(..., description="Content of the message")
    tool_call_id: Optional[str] = Field(None, description="ID of the tool call (for tool messages)")
    tool_name: Optional[str] = Field(None, description="Name of the tool (for tool messages)")


class ChatRequest(BaseModel):
    """Model for incoming chat requests."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")


class ChatResponse(BaseModel):
    """Model for chat API responses."""
    messages: List[Message] = Field(..., description="List of messages in the conversation")
    session_id: str = Field(..., description="Session ID for conversation continuity")
    error: Optional[str] = Field(None, description="Error message if something went wrong")