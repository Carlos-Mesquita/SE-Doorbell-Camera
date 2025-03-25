from abc import ABC

from doorbell_api.dtos import SettingsDTO, NotificationDTO, CaptureDTO
from doorbell_api.models import Settings, Notification, Capture

from .base import IBaseService


class ISettingsService(IBaseService[SettingsDTO, Settings], ABC):
    pass

class INotificationService(IBaseService[NotificationDTO, Notification], ABC):
    pass

class ICaptureService(IBaseService[CaptureDTO, Capture], ABC):
    pass
