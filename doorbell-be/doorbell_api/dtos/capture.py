from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CaptureDTO(BaseModel):
    id: Optional[int] = None
    notification_id: Optional[int] = None
    path: str
    created_at: datetime
