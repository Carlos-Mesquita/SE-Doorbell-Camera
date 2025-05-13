from abc import ABC, abstractmethod
from asyncio import Queue
from typing import Dict, Any


class IMessageHandler(ABC):

    @abstractmethod
    async def handle_camera_events(self, message: any, jwt_payload: Dict[str, any], message_queue: Queue) -> Dict[str, Any]:
        pass
