from typing import Optional
from pydantic import BaseModel

class FCMDeviceRegistrationDTO(BaseModel):
    fcm_token: str
    physical_device_id: str
    device_type: Optional[str] = None
    app_version: Optional[str] = None
