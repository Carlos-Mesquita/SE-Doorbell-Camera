from abc import ABC

from ...dtos import NotificationDTO, SettingsDTO, CaptureDTO

from .base import IBaseController

class INotificationController(IBaseController[NotificationDTO], ABC):
    pass

class ICaptureController(IBaseController[CaptureDTO], ABC):
    pass

class ISettingsController(IBaseController[SettingsDTO], ABC):
    pass
