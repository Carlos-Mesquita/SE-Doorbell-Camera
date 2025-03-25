from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CaptureDTO(BaseModel):
    id: Optional[int] = None
    notification_id: int
    path: str
    created_at: datetime
