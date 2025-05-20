from abc import ABC, abstractmethod
from typing import Optional, List, Any

from . import IBaseRepository


class IFCMDeviceRepository(IBaseRepository[Any], ABC):
    @abstractmethod
    async def get_by_user_and_physical_id(self, user_id: int, physical_device_id: str) -> Optional[Any]:
        pass

    @abstractmethod
    async def create_fcm_device(
        self, user_id: int, fcm_token: str, physical_device_id: str, device_type: Optional[str], app_version: Optional[str]
    ) -> Any:
        pass

    @abstractmethod
    async def update_fcm_device_token(
            self, device_id: int, new_fcm_token: str, new_app_version: Optional[str]
    ) -> Optional[Any]:
        pass

    @abstractmethod
    async def delete_by_user_and_physical_id(self, user_id: int, physical_device_id: str) -> bool:
        pass

    @abstractmethod
    async def get_tokens_by_user_id(self, user_id: int) -> List[str]:
        pass
