from enum import Enum, auto

class SettingsEvent(Enum):
    CHANGE_MOTION_SENSOR_DEBOUNCE = auto()
    CHANGE_MOTION_SENSOR_POLLING = auto()

    CHANGE_BUTTON_DEBOUNCE = auto()
    CHANGE_BUTTON_POLLING = auto()

    CHANGE_LED_COLOR = auto()

    CHANGE_CAMERA_BITRATE = auto()
    CHANGE_STOP_MOTION_INTERVAL = auto()
    CHANGE_STOP_MOTION_DURATION = auto()

    RETRIEVE_CONFIGS = auto()
