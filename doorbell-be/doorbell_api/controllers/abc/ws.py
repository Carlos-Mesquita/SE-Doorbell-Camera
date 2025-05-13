from abc import ABC, abstractmethod
from fastapi.websockets import WebSocket


class IWebSocketController(ABC):

    @abstractmethod
    async def process_camera(self, websocket: WebSocket, access_token: str):
        pass

    @abstractmethod
    async def push_notifications(self, websocket: WebSocket, access_token: str):
        pass

    @abstractmethod
    async def handle_signaling(self, websocket: WebSocket, access_token: str):
        pass
