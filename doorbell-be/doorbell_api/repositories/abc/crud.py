from abc import ABC

from doorbell_api.models import Settings, Capture, Notification
from .base import IBaseRepository


class ISettingsRepository(IBaseRepository[Settings], ABC):
    pass


class ICaptureRepository(IBaseRepository[Capture], ABC):
    pass

class INotificationRepository(IBaseRepository[Notification], ABC):
    pass
