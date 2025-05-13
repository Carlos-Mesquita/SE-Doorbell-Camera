from datetime import datetime

from pydantic import BaseModel, Field

class Capture(BaseModel):
    associated_to: str
    timestamp: datetime = Field(default_factory=datetime.now)
    path: str
