from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from doorbell_api.dtos import SettingsDTO, NotificationDTO, CaptureDTO
from doorbell_api.models import Settings, Notification, Capture

from .base import IBaseService


class ISettingsService(IBaseService[SettingsDTO, Settings], ABC):
    pass

class INotificationService(IBaseService[NotificationDTO, Notification], ABC):

    @abstractmethod
    async def create_notification(self, notification_payload_dict: Dict[str, Any], user_id_for_fcm_lookup: Optional[int]) -> Optional[Dict[str, Any]]:
        pass


class ICaptureService(IBaseService[CaptureDTO, Capture], ABC):
    pass
