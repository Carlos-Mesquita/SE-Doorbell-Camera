from abc import ABC, abstractmethod

class ICamera(ABC):

    @abstractmethod
    def start_stream(self):
        pass

    @abstractmethod
    def stop_stream(self):
        pass

    @abstractmethod
    def begin_stop_motion(self, e_id: str):
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
