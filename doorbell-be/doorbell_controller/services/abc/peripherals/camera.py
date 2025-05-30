from abc import ABC, abstractmethod
from typing import Dict, Any


class ICamera(ABC):

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def begin_stop_motion(self, event_id: str = None):
        pass

    @abstractmethod
    def end_stop_motion(self):
        pass

    @abstractmethod
    async def get_streaming_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def set_stop_motion_interval(self, value_seconds: float) -> None:
        pass

    @abstractmethod
    async def get_stop_motion_interval(self) -> float:
        pass
