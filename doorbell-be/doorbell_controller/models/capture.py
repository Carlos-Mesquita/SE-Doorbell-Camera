from datetime import datetime

from pydantic import BaseModel, Field

class Capture(BaseModel):
    id: str
    associated_to: str
    timestamp: datetime = Field(default_factory=datetime.now)
    image_data: bytes
    image_format: str
    has_face: bool

    model_config = {
        "arbitrary_types_allowed": True
    }
