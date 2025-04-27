from fastapi import APIRouter, WebSocket
from api.controllers.chat_controller import websocket_endpoint

# Create router
router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint_route(websocket: WebSocket, client_id: str):
    """Handle WebSocket connections for chat functionality."""
    return await websocket_endpoint(websocket, client_id)


