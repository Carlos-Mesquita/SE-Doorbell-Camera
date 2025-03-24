from abc import ABC, abstractmethod
from typing import TypeAlias, Union

from .sensor import ISensor
from .rgb import IRGB
from .camera import ICamera


class IPeripheral(ABC):

    @abstractmethod
    def cleanup(self):
        pass


SensorService: TypeAlias = Union[IPeripheral, ISensor]
RGBService: TypeAlias = Union[IPeripheral, IRGB]
CameraService: TypeAlias = Union[IPeripheral, ICamera]

__all__ = [
    "IPeripheral",
    "IRGB",
    "ISensor",
    "ICamera",
    "SensorService",
    "RGBService",
    "CameraService"
]
