from abc import ABC, abstractmethod

from ...dtos import NotificationDTO, SettingsDTO, CaptureDTO

from .base import IBaseController

class INotificationController(IBaseController[NotificationDTO], ABC):
    pass

class ICaptureController(IBaseController[CaptureDTO], ABC):
    @abstractmethod
    async def generate_cap_video(self, ids: list[str]):
        pass

class ISettingsController(IBaseController[SettingsDTO], ABC):
    pass
