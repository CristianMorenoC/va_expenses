from api.models.ws_connection_manager import IConnectionManager

from fastapi import WebSocket

class ConnectionManager(IConnectionManager):
    def __init__(self):
        # Store connections mapping client_id -> WebSocket
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        # Remove the specific client's connection
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        # Send a message only to the specific client
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            await websocket.send_text(message)

    # Optional: Keep broadcast if needed for system-wide messages,
    # but use it carefully as it goes to ALL connected users.
    async def broadcast(self, message: str):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)

manager = ConnectionManager()
