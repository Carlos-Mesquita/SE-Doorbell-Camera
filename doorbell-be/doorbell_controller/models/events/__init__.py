from uuid import uuid4
from datetime import datetime
from enum import Enum
from typing import TypeVar, Optional, Dict, Generic

from pydantic import BaseModel, Field

EventType = TypeVar('EventType', bound=Enum)

class Event(BaseModel, Generic[EventType]):
    model_config = {
        "arbitrary_types_allowed": True
    }

    type: EventType
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    source_device_id: Optional[str] = None
    payload: Optional[Dict[str, any]] = None

from .sensor import SensorEvent
from .settings import SettingsEvent

__all__ = [
    "Event",
    "SensorEvent",
    "SettingsEvent"
]
