from abc import abstractmethod, ABC
from typing import List

from starlette.websockets import WebSocket


class IWebRTCSignalingService(ABC):
    @abstractmethod
    async def register_client(self, client_id: str, websocket: WebSocket, user_id: str) -> None:
        pass

    @abstractmethod
    async def unregister_client(self, client_id: str) -> None:
        pass

    @abstractmethod
    async def handle_message(self, client_id: str, message: dict) -> dict:
        pass

    @abstractmethod
    async def join_room(self, client_id: str, room_id: str, role: str = "viewer") -> dict:
        pass

    @abstractmethod
    async def leave_room(self, client_id: str, room_id: str) -> dict:
        pass

    @abstractmethod
    def get_active_rooms(self) -> List[dict]:
        pass

    @abstractmethod
    def get_room_clients(self, room_id: str) -> List[dict]:
        pass
