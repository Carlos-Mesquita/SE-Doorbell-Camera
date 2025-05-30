from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from ..dtos import CaptureDTO


class NotificationDTO(BaseModel):
    id: Optional[int] = None
    title: str
    created_at: Optional[datetime] = None
    captures: Optional[List[CaptureDTO]] = Field(default_factory=list)

    rpi_event_id: Optional[str] = None
    type_str: Optional[str] = None
    user_id: Optional[int] = None

    model_config = ConfigDict(use_enum_values=True)
