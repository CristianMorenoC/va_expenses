from fastapi import HTTPException
from main_graph import get_agent_graph as get_original_agent_graph

def get_agent():
    """
    Get the financial assistant agent graph.
    This service centralizes agent graph access to avoid circular imports.
    """
    try:
        return get_original_agent_graph()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}") 