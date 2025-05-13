from logging import getLogger
from typing import Dict, Any
from firebase_admin import messaging

from doorbell_api.dtos import NotificationDTO
from doorbell_api.models import Notification
from doorbell_api.services import INotificationService
from doorbell_api.repositories import INotificationRepository

from doorbell_api.mappers import IMapper

from .base import BaseService

class NotificationService(BaseService[NotificationDTO, Notification], INotificationService):
    def __init__(self, mapper: IMapper[NotificationDTO, Notification], repo: INotificationRepository):
        super().__init__(mapper, repo)
        self._repo = repo
        self._logger = getLogger(__name__)

    async def create_notification(self, message: Dict[str, Any]):
        notification_dto = await super().create(NotificationDTO(**message))
        self._send_to_fcm(notification_dto.model_dump_json())

    def _send_to_fcm(self, notification_data: Dict[str, Any], token: str):
        try:
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=notification_data.get("title"),
                ),
                data=notification_data,
                token=token,
            )

            response = messaging.send(fcm_message)
            return response
        except Exception as e:
            self._logger.error(f"Error sending FCM notification: {e}")
            return None
