import enum
import json
from datetime import datetime


class MessageTypeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, enum.Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class MessageType(enum.Enum):
    PING = 1
    PONG = 2

    AUTH = 3
    AUTH_RESULT = 4

    MOTION_DETECTED = 5
    FACE_DETECTED = 6
    BUTTON_PRESSED = 7

    STREAM_START = 8
    STREAM_STOP = 9
    STREAM_ACK = 10

    SETTINGS_REQUEST = 11
    SETTINGS_ACK = 12

    NOTIFICATION_ACK = 13
    NOTIFICATION_SYNC = 14
    NOTIFICATION_SYNC_RESPONSE = 15

    CAPTURE = 16
    CAPTURE_ACK = 17

    ERROR = 18
