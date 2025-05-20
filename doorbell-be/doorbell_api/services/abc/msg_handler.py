from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING, Optional

class IMessageHandler(ABC):

    @abstractmethod
    async def handle_camera_events(self, message: Any, jwt_payload: Dict[str, any]) -> Optional[Dict[str, Any]]:
        pass
