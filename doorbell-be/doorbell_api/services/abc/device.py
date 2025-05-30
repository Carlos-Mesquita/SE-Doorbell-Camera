from abc import ABC, abstractmethod

class IDeviceService(ABC):

    @abstractmethod
    async def register_or_update_fcm_device(
        self,
        user_id: int,
        fcm_token: str,
        physical_device_id: str,
    ) -> None:
        pass

    @abstractmethod
    async def get_fcm_tokens_for_user(self, user_id: int) -> list[str]:
        pass
