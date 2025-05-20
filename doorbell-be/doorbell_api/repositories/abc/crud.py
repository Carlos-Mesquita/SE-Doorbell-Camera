from abc import ABC, abstractmethod
from typing import Optional

from ...models import Settings, Capture, Notification
from .base import IBaseRepository


class ISettingsRepository(IBaseRepository[Settings], ABC):
    pass


class ICaptureRepository(IBaseRepository[Capture], ABC):
    pass

class INotificationRepository(IBaseRepository[Notification], ABC):

    @abstractmethod
    async def find_by_rpi_event_id(self, rpi_event_id: str, user_id: Optional[str] = None) -> Optional[Notification]:
        pass

