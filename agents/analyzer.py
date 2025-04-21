from typing import Dict, Any, List
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.output_parsers import JsonOutputParser

from config import LLM_MODEL

ANALYZER_SYSTEM_PROMPT = """You are an expert financial intent analyzer. 
Your job is to understand what the user is asking about their finances and categorize their query.

The possible categories are:
1. ADD_EXPENSE - User wants to add a new expense
2. ADD_INCOME - User wants to add income
3. GET_SUMMARY - User wants a summary of their expenses
4. CREATE_BUDGET - User wants to create or adjust their budget
5. ANALYZE_TREND - User wants to analyze spending trends
6. GENERAL_ADVICE - User wants general financial advice

For ADD_EXPENSE and ADD_INCOME, extract the relevant fields:
- amount: the numerical amount
- category/source: the category of expense or source of income
- description: a brief description
- date: the date if mentioned (use ISO format YYYY-MM-DD)

Return your analysis as a structured JSON with the following format:
{
  "intent": "INTENT_CATEGORY",
  "confidence": 0.0 to 1.0,
  "extracted_data": {
    // Any relevant extracted fields
  }
}
"""

class IntentAnalyzer:
    """Analyzes user messages to determine their financial intent."""
    
    def __init__(self):
        self.llm = ChatAnthropic(model=LLM_MODEL, temperature=0)
        self.parser = JsonOutputParser()
        
    def analyze(self, user_message: str, chat_history: List = None) -> Dict[str, Any]:
        """
        Analyze the user's message to determine their intent.
        
        Args:
            user_message: The user's input message
            chat_history: Optional chat history for context
            
        Returns:
            A dictionary with the detected intent and extracted data
        """
        messages = [
            SystemMessage(content=ANALYZER_SYSTEM_PROMPT),
            HumanMessage(content=user_message)
        ]
        
        # If chat history is provided, add it for context
        if chat_history:
            context_messages = []
            for msg in chat_history[-5:]:  # Use last 5 messages for context
                if isinstance(msg, HumanMessage):
                    context_messages.append(f"User: {msg.content}")
                elif isinstance(msg, AIMessage):
                    context_messages.append(f"Assistant: {msg.content}")
            
            if context_messages:
                context = "\n".join(context_messages)
                messages.insert(1, SystemMessage(content=f"Chat history context:\n{context}"))
        
        response = self.llm.invoke(messages)
        
        try:
            # Extract JSON from the response
            json_str = response.content
            # Handle potential issues with the JSON format
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            return self.parser.parse(json_str)
        except Exception as e:
            return {
                "intent": "ERROR",
                "confidence": 0.0,
                "error": str(e),
                "raw_response": response.content
            }

# Usage example:
# analyzer = IntentAnalyzer()
# result = analyzer.analyze("I spent $50 on groceries yesterday")
# print(result) 