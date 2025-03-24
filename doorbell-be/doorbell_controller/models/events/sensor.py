from enum import Enum, auto

class SensorEvent(Enum):
    MOTION_DETECTED = auto()
    BUTTON_PRESSED = auto()
    FACE_DETECTED = auto()
