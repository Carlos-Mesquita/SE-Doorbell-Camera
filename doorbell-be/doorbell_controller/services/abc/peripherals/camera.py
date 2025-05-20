from abc import ABC, abstractmethod
from typing import Dict, Any


class ICamera(ABC):

    @abstractmethod
    def start_stream(self):
        pass

    @abstractmethod
    def stop_stream(self):
        pass

    @abstractmethod
    def begin_stop_motion(self):
        pass

    @abstractmethod
    def end_stop_motion(self):
        pass

    @property
    @abstractmethod
    def bitrate(self) -> int:
        pass

    @bitrate.setter
    @abstractmethod
    def bitrate(self, value: int):
        pass

    @property
    @abstractmethod
    def interval(self) -> float:
        pass

    @interval.setter
    @abstractmethod
    def interval(self, value: float):
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
