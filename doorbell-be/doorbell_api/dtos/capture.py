from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CaptureDTO(BaseModel):
    id: Optional[int] = None
    notification_id: Optional[int] = None
    path: str
    created_at: datetime = Field(default_factory=datetime.now)
