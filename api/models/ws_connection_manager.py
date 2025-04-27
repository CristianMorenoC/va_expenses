from fastapi import WebSocket
from abc import ABC, abstractmethod

class IConnectionManager(ABC):
    """Interface defining the contract for WebSocket connection management."""
    
    @abstractmethod
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Accept a new websocket connection and add it to active connections."""
        pass

    @abstractmethod
    def disconnect(self, client_id: str) -> None:
        """Remove a websocket connection from active connections."""
        pass

    @abstractmethod
    async def send_personal_message(self, message: str, client_id: str) -> None:
        """Send a message to a specific websocket connection."""
        pass

    @abstractmethod
    async def broadcast(self, message: str) -> None:
        """Broadcast a message to all active websocket connections."""
        pass



