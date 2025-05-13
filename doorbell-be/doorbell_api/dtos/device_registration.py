from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from doorbell_api.dtos import CaptureDTO


class DeviceRegistrationDTO(BaseModel):
    user_id: Optional[int] = None
    title: str
    created_at: datetime
    captures: Optional[List[CaptureDTO]] = None