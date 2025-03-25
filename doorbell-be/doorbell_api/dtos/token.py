from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TokenDTO(BaseModel):
    id: Optional[int] = None
    guid: UUID
    created_at: datetime
    expires_at: Optional[datetime]
