from enum import Enum, auto

class SettingsEvent(Enum):
    CHANGE_SETTINGS = auto()
    GET_SETTINGS = auto()
