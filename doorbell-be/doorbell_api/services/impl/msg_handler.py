import uuid
from asyncio import Queue
from typing import Dict, Optional, List
import logging
from datetime import datetime

from doorbell_api.services import IMessageHandler, INotificationService
from doorbell_shared.models import Message, MessageType


class MessageHandler(IMessageHandler):

    def __init__(self, notification_service: INotificationService):
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)

    async def handle_camera_events(self, message: Message, jwt_payload: Dict[str, any], message_queue: Queue):
        try:
            if message.msg_type in [
                MessageType.MOTION_DETECTED.value,
                MessageType.FACE_DETECTED.value,
                MessageType.BUTTON_PRESSED.value,
                MessageType.FACE_DETECTED.value,
            ]:
                notification_data = await self._create_notification(message)

                if notification_data:
                    await message_queue.put({
                        "type": "notification",
                        "timestamp": datetime.now().isoformat()
                    })

                    await message_queue.put({
                        "type": "response",
                        "message": Message.create_response(
                            original_msg=message,
                            msg_type=MessageType.NOTIFICATION_ACK,
                            payload={"status": "processed"}
                        )
                    })

        except Exception as e:
            self.logger.error(f"Error processing notification: {e}")
            await message_queue.put({
                "type": "response",
                "message": Message.create_response(
                    original_msg=message,
                    msg_type=MessageType.ERROR,
                    payload={"error": str(e)}
                )
            })

    async def _create_notification(self, message: Message) -> Optional[Dict]:
        if message.msg_type == MessageType.MOTION_DETECTED.value:
            notification_type = "motion_detected"
            title = "Motion Detected"
        elif message.msg_type == MessageType.FACE_DETECTED.value:
            notification_type = "face_detected"
            title = "Face Detected"
        elif message.msg_type == MessageType.BUTTON_PRESSED.value:
            notification_type = "button_pressed"
            title = "Doorbell Pressed"
        else:
            return None

        notification_data = {
            "id": (uuid.uuid4()),
            "type": notification_type,
            "title": title,
            "timestamp": datetime.now().isoformat()
        }

        if message.payload:
            notification_data.update(message.payload)

        await self.notification_service.create_notification(notification_data)

        return notification_data

    async def _save_capture(self, capture: bytes) -> str:
        # TODO: figure out a way to distinguish messages from raw bytes, save it to the fs return path and associate it with the notification
        raise NotImplementedError()

    async def _get_notification_history(self, limit: int = 10, offset: int = 0) -> List[Dict]:
        return await self.notification_service.get_all(limit, offset)
