import base64
import os
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any
import enum

from logging import getLogger
from dependency_injector.wiring import Provide, inject

from doorbell_api.dtos import CaptureDTO
from doorbell_api.repositories import INotificationRepository
from doorbell_api.services import IMessageHandler, INotificationService, ICaptureService
from doorbell_shared.models import Message, MessageType

RP_I_OWNER_USER_ID_FOR_FCM: int = 1  # TODO: Hardcoded, implement a proper way to do this


class MessageHandler(IMessageHandler):

    @inject
    def __init__(
            self,
            notification_service: INotificationService = Provide['notification_service'],
            capture_service: ICaptureService = Provide['capture_service'],
            notification_repo: INotificationRepository = Provide['notification_repo'],
            config: dict[str, Any] = Provide['config']
    ):
        self.notification_service = notification_service
        self.capture_service = capture_service
        self.notification_repo = notification_repo
        self.captures_base_path = Path(config['capture_dir'])
        self.captures_base_path.mkdir(parents=True, exist_ok=True)
        self.logger = getLogger(__name__)

        # Rate limiting configuration
        self.motion_rate_limit_minutes = config.get('motion_rate_limit_minutes', 1)

    async def handle_camera_events(self, message: Message, jwt_payload: Dict[str, any]) -> Optional[Dict[str, Any]]:
        try:
            response_payload: Optional[Dict[str, Any]] = None
            response_type = MessageType.ERROR

            target_user_id_for_fcm: Optional[int] = None
            user_id_str_for_payloads: Optional[str] = None

            id_from_rpi_token = jwt_payload.get('sub', '')

            if id_from_rpi_token == "rpi":
                target_user_id_for_fcm = RP_I_OWNER_USER_ID_FOR_FCM
                user_id_str_for_payloads = str(RP_I_OWNER_USER_ID_FOR_FCM)
                self.logger.info(
                    f"RPi event (token id: '{id_from_rpi_token}') mapped to owner User ID: {target_user_id_for_fcm} for FCM."
                )
            elif id_from_rpi_token.isdigit():
                target_user_id_for_fcm = int(id_from_rpi_token)
                user_id_str_for_payloads = id_from_rpi_token
                self.logger.info(f"RPi event from user-specific token. User ID: {target_user_id_for_fcm} for FCM.")
            else:
                self.logger.warning(
                    f"RPi token decoded to '{id_from_rpi_token}', cannot determine target user for FCM."
                )
                response_payload = {"error": "Cannot determine RPi owner user."}

            if response_payload is None:
                if message.msg_type in [MessageType.MOTION_DETECTED, MessageType.FACE_DETECTED,
                                        MessageType.BUTTON_PRESSED]:
                    if message.msg_type == MessageType.MOTION_DETECTED:
                        should_process = await self.notification_repo.is_rate_limited(user_id_str_for_payloads)
                        if not should_process:
                            self.logger.info(
                                f"Motion event rate limited for user {user_id_str_for_payloads}. "
                                f"Less than {self.motion_rate_limit_minutes} minute(s) since last notification."
                            )
                            response_payload = {
                                "status": "rate_limited",
                                "message": f"Motion notifications are rate limited to {self.motion_rate_limit_minutes} minute(s)"
                            }
                            response_type = MessageType.NOTIFICATION_ACK

                    if response_payload is None:
                        notification_payload_for_dto = await self._create_notification_payload(message,user_id=user_id_str_for_payloads)
                        if notification_payload_for_dto:
                            created_notification_info = await self.notification_service.create_notification(
                                notification_payload_for_dto, user_id_for_fcm_lookup=target_user_id_for_fcm
                            )
                            if created_notification_info and "id" in created_notification_info:
                                notification_db_id_for_linking_capture = created_notification_info.get("id")
                                response_payload = {
                                    "status": "processed",
                                    "notification_id": str(notification_db_id_for_linking_capture)
                                }
                                response_type = MessageType.NOTIFICATION_ACK
                            else:
                                response_payload = {"error": "Failed to finalize notification"}
                        else:
                            response_payload = {"error": "Failed to prepare notification data"}

                elif message.msg_type == MessageType.CAPTURE:
                    self.logger.info(f"Received CAPTURE from RPi, intended for user context: {target_user_id_for_fcm}")
                    if message.payload and "image_data_b64" in message.payload:
                        rpi_event_id_for_capture = message.payload.get("associated_to")
                        actual_notification_id_to_link: Optional[int] = None

                        if rpi_event_id_for_capture and self.notification_repo:
                            notification_obj = await self.notification_repo.find_by_rpi_event_id(
                                rpi_event_id_for_capture, user_id_str_for_payloads
                            )
                            if notification_obj:
                                actual_notification_id_to_link = notification_obj.id
                                self.logger.info(
                                    f"Found Notification DB ID {actual_notification_id_to_link} to link capture for RPi event {rpi_event_id_for_capture}")
                            else:
                                self.logger.warning(
                                    f"CAPTURE: No Notification found for RPi event ID {rpi_event_id_for_capture} and user {user_id_str_for_payloads}. Capture will be unlinked.")
                        else:
                            self.logger.warning(
                                "CAPTURE: RPi event ID missing or notification_repo not available. Cannot link to notification by RPi event ID.")

                        saved_capture_info = await self._save_capture_from_payload(
                            message.payload, user_id_str_for_dto=user_id_str_for_payloads,
                            notification_db_id_to_link=actual_notification_id_to_link
                        )

                        if saved_capture_info:
                            response_payload = {
                                "status": "capture_received_and_saved",
                                "capture_id": str(saved_capture_info.get("id"))
                            }
                            if actual_notification_id_to_link is not None:
                                response_payload["linked_to_notification_id"] = str(actual_notification_id_to_link)
                            response_type = MessageType.CAPTURE_ACK
                        else:
                            response_payload = {"error": "Failed to save capture data"}
                    else:
                        response_payload = {"error": "Capture message missing image_data_b64"}
                else:
                    self.logger.warning(f"Unhandled message type from RPi: {message.msg_type}")
                    type_name = message.msg_type.name if isinstance(message.msg_type, enum.Enum) else str(
                        message.msg_type)
                    response_payload = {"error": f"Unhandled message type: {type_name}"}

            if response_payload is None and response_type == MessageType.ERROR:
                response_payload = {"error": "Unknown processing error in MessageHandler"}

            return Message.create_response(
                original_msg=message, msg_type=response_type, payload=response_payload
            ).model_dump(exclude_none=True)
        except Exception as e:
            self.logger.error(
                f"Critical error in MessageHandler.handle_camera_events for msg_type {message.msg_type}: {e}",
                exc_info=True
            )
            return Message.create_response(
                original_msg=message, msg_type=MessageType.ERROR, payload={"error": f"Server critical error: {str(e)}"}
            ).model_dump(exclude_none=True)

    async def _create_notification_payload(self, message: Message, user_id: Optional[str]) -> Optional[Dict]:
        rpi_event_id_to_store: Optional[str] = message.msg_id

        if message.msg_type == MessageType.MOTION_DETECTED:
            notification_type_str = "motion_detected"
            title = "Motion Detected"
        elif message.msg_type == MessageType.FACE_DETECTED:
            notification_type_str = "face_detected"
            title = "Face Detected"
        elif message.msg_type == MessageType.BUTTON_PRESSED:
            notification_type_str = "button_pressed"
            title = "Doorbell Pressed"
        else:
            self.logger.warning(f"Cannot create notification payload for unknown message type: {message.msg_type}")
            return None

        payload_for_dto = {
            "title": title,
            "rpi_event_id": rpi_event_id_to_store,
            "type_str": notification_type_str,
            "user_id": user_id,
            "timestamp": datetime.now(),
        }
        return payload_for_dto

    async def _save_capture_from_payload(self, capture_payload: Dict, user_id_str_for_dto: Optional[str],
                                         notification_db_id_to_link: Optional[int]) -> Optional[Dict[str, Any]]:
        try:
            image_b64_data = capture_payload.get("image_data_b64")
            if not image_b64_data:
                self.logger.error("No image_data")
                return None
            image_bytes = base64.b64decode(image_b64_data)

            capture_datetime = datetime.now()
            timestamp_str = capture_payload.get("timestamp")
            if timestamp_str:
                try:
                    capture_datetime = datetime.fromisoformat(timestamp_str)
                except ValueError:
                    self.logger.warning(f"Bad capture timestamp '{timestamp_str}'")

            file_stem = f"capture_{capture_datetime.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex}"

            with tempfile.NamedTemporaryFile(suffix='.yuv', delete=False) as temp_yuv:
                temp_yuv.write(image_bytes)
                temp_yuv_path = temp_yuv.name

            try:
                file_name = f"{file_stem}.png"
                file_path_on_fs = self.captures_base_path / file_name
                path_for_db_or_dto = file_name

                cmd = [
                    'ffmpeg',
                    '-f', 'rawvideo',
                    '-pix_fmt', 'yuv420p',
                    '-s', '1280x720',
                    '-i', temp_yuv_path,
                    '-vframes', '1',
                    '-y',
                    str(file_path_on_fs)
                ]

                subprocess.run(cmd, check=True, capture_output=True)

            finally:
                os.unlink(temp_yuv_path)

            self.logger.info(f"Capture image saved to FS: {file_path_on_fs}")

            if self.capture_service:
                capture_dto_data = {
                    "path": path_for_db_or_dto,
                    "timestamp": capture_datetime,
                    "user_id": user_id_str_for_dto,
                    "notification_id": notification_db_id_to_link
                }

                try:
                    dto_instance = CaptureDTO(**capture_dto_data)
                except Exception as pydantic_exc:
                    self.logger.error(
                        f"Pydantic validation error for CaptureDTO: {pydantic_exc}. Data: {capture_dto_data}"
                    )
                    return None

                created_capture_dto = await self.capture_service.create(dto_instance)
                self.logger.info(
                    f"Capture record created in DB: ID {created_capture_dto.id}, linked to Notification ID: {notification_db_id_to_link}"
                )
                return {"id": created_capture_dto.id, "path": created_capture_dto.path}
            else:
                self.logger.warning("CaptureService not available. Capture image saved to FS but no DB record created.")
                return {"id": None, "path": path_for_db_or_dto, "status": "saved_to_fs_only_no_service"}

        except Exception as e:
            self.logger.error(f"Error in _save_capture_from_payload: {e}", exc_info=True)
            return None
