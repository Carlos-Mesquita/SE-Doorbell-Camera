from abc import ABC, abstractmethod
from typing import Optional

class IDeviceService(ABC):

    @abstractmethod
    async def register_or_update_fcm_device(
        self,
        user_id: int,
        fcm_token: str,
        physical_device_id: str,
        device_type: Optional[str] = None,
        app_version: Optional[str] = None
    ) -> None:
        pass

    @abstractmethod
    async def get_fcm_tokens_for_user(self, user_id: int) -> list[str]:
        pass
