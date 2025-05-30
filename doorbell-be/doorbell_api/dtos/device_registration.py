from pydantic import BaseModel

class FCMDeviceRegistrationDTO(BaseModel):
    fcm_token: str
    physical_device_id: str

