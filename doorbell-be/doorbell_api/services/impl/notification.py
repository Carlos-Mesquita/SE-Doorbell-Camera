from logging import getLogger
from typing import Dict, Any, Optional
from firebase_admin import messaging
from dependency_injector.wiring import inject, Provide

from doorbell_api.dtos import NotificationDTO
from doorbell_api.models import Notification
from doorbell_api.services import INotificationService, IDeviceService
from doorbell_api.repositories import INotificationRepository
from doorbell_api.mappers import IMapper
from .base import BaseService


class NotificationService(BaseService[NotificationDTO, Notification], INotificationService):
    @inject
    def __init__(self,
        mapper: IMapper[NotificationDTO, Notification] = Provide['notification_mapper'],
        repo: INotificationRepository = Provide['notification_repo'],
        device_service: IDeviceService = Provide['device_service'],
    ):
        super().__init__(mapper, repo)
        self._repo = repo
        self._device_service = device_service
        self._logger = getLogger(__name__)

    async def create_notification(self, notification_payload_dict: Dict[str, Any], user_id_for_fcm_lookup: Optional[int]) -> Optional[Dict[str, Any]]:
        try:
            if 'user_id' not in notification_payload_dict and user_id_for_fcm_lookup:
                notification_payload_dict['user_id'] = str(user_id_for_fcm_lookup)

            notification_dto = NotificationDTO(**notification_payload_dict)
            created_dto_from_db = await super().create(notification_dto)
            self._logger.info(
                f"Notification DB record created: ID {created_dto_from_db.id} for RPi Event ID {created_dto_from_db.rpi_event_id}"
            )

            if user_id_for_fcm_lookup:
                fcm_tokens = await self._device_service.get_fcm_tokens_for_user(user_id_for_fcm_lookup)
                if fcm_tokens:
                    self._logger.info(
                        f"Found {len(fcm_tokens)} FCM tokens for user {user_id_for_fcm_lookup}. Sending notifications.")

                    fcm_data_payload = {
                        k: str(v) for k, v in
                        created_dto_from_db.model_dump(exclude_none=True, by_alias=False).items() if
                        v is not None
                    }
                    title_for_fcm = str(notification_payload_dict.get("title", "Doorbell Alert"))

                    for token in fcm_tokens:
                        self._send_to_fcm(
                            title=title_for_fcm,
                            data_payload=fcm_data_payload,
                            device_token=token
                        )
                else:
                    self._logger.info(f"No active FCM tokens found for user {user_id_for_fcm_lookup}.")
            else:
                self._logger.warning("No user_id_for_fcm_lookup provided to create_notification, cannot send FCM.")

            return created_dto_from_db.model_dump(exclude_none=True, by_alias=False)
        except Exception as e:
            self._logger.error(f"Error in NotificationService.create_notification: {e}", exc_info=True)
            return None

    def _send_to_fcm(self, title: str, data_payload: Dict[str, str], device_token: str):
        try:
            message = messaging.Message(
                notification=messaging.Notification(title=title),
                data=data_payload,
                token=device_token,
            )
            response = messaging.send(message)
            return response
        except Exception as e:
            self._logger.error(f"Error sending FCM to token {device_token[:10]}...: {e}", exc_info=True)
            return None
