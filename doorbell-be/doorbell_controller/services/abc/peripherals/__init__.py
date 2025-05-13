from abc import ABC, abstractmethod
from typing import TypeAlias, Union

from .sensor import ISensor
from .rgb import IRGB
from .camera import ICamera


class IPeripheral(ABC):

    @abstractmethod
    async def cleanup(self):
        pass


ISensorService: TypeAlias = Union[IPeripheral, ISensor]
IRGBService: TypeAlias = Union[IPeripheral, IRGB]
ICameraService: TypeAlias = Union[IPeripheral, ICamera]

__all__ = [
    "IPeripheral",
    "IRGB",
    "ISensor",
    "ICamera",
    "ISensorService",
    "IRGBService",
    "ICameraService"
]
