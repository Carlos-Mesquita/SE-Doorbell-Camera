from datetime import datetime
from enum import Enum
from typing import TypeVar, Optional, Dict

from pydantic import BaseModel, Field

EventType = TypeVar('EventType', bound=Enum)

class Event(BaseModel):
    type: EventType
    timestamp: datetime = Field(default_factory=datetime.now)
    payload: Optional[Dict[str, any]] = None

from .sensor import SensorEvent
from .settings import SettingsEvent

__all__ = [
    "Event",
    "SensorEvent",
    "SettingsEvent"
]
