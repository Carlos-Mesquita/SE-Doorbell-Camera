from enum import Enum, auto


class ControllerState(Enum):
    IDLE = auto()
    STREAMING = auto()
    RECORDING = auto()
