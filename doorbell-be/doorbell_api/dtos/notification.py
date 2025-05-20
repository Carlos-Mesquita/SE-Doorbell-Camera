from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from ..dtos import CaptureDTO


class NotificationDTO(BaseModel):
    id: Optional[int] = None
    title: str
    created_at: Optional[datetime] = None
    captures: Optional[List[CaptureDTO]] = None

    rpi_event_id: Optional[str] = None
    type_str: Optional[str] = None
    user_id: Optional[int] = None

    model_config = {
        "from_attributes": True
    }