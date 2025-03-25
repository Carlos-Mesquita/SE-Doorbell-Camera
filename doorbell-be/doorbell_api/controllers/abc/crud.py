from abc import ABC

from doorbell_api.dtos import NotificationDTO, SettingsDTO, CaptureDTO

from .base import IBaseController

class INotificationController(IBaseController[NotificationDTO], ABC):
    pass

class ICaptureController(IBaseController[CaptureDTO], ABC):
    pass

class ISettingsController(IBaseController[SettingsDTO], ABC):
    pass
