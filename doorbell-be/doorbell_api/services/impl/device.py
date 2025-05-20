import logging
from typing import Optional, List

from ...configs.db import Transactional
from ...services import IDeviceService
from ...repositories import IFCMDeviceRepository

logger = logging.getLogger(__name__)

class DeviceService(IDeviceService):
    def __init__(self, fcm_device_repo: IFCMDeviceRepository):
        self._fcm_device_repo = fcm_device_repo


    @Transactional()
    async def register_or_update_fcm_device(
        self,
        user_id: int,
        fcm_token: str,
        physical_device_id: str,
        device_type: Optional[str] = None,
        app_version: Optional[str] = None
    ) -> None:
        try:
            existing_device = await self._fcm_device_repo.get_by_user_and_physical_id(
                user_id=user_id,
                physical_device_id=physical_device_id
            )

            if existing_device:
                if existing_device.fcm_token != fcm_token or existing_device.app_version != app_version:
                    logger.info(f"Updating FCM token for user {user_id}, device {physical_device_id}")
                    await self._fcm_device_repo.update_fcm_device_token(
                        device_id=existing_device.id,
                        new_fcm_token=fcm_token,
                        new_app_version=app_version
                    )
                else:
                    logger.debug(f"FCM token for user {user_id}, device {physical_device_id} is current. Updating last_seen.")
                    await self._fcm_device_repo.update_fcm_device_token(
                        device_id=existing_device.id, new_fcm_token=fcm_token, new_app_version=app_version
                    )
            else:
                logger.info(f"Registering new FCM device for user {user_id}, device {physical_device_id}")
                await self._fcm_device_repo.create_fcm_device(
                    user_id=user_id,
                    fcm_token=fcm_token,
                    physical_device_id=physical_device_id,
                    device_type=device_type,
                    app_version=app_version
                )
        except Exception as e:
            logger.error(f"Error in register_or_update_fcm_device for user {user_id}: {e}", exc_info=True)
            raise

    async def unregister_fcm_device(
        self,
        user_id: int,
        physical_device_id: str
    ) -> None:
        try:
            success = await self._fcm_device_repo.delete_by_user_and_physical_id(
                user_id=user_id,
                physical_device_id=physical_device_id
            )
            if success:
                logger.info(f"Unregistered FCM device for user {user_id}, physical_device_id {physical_device_id}")
            else:
                logger.warning(f"Attempt to unregister non-existent FCM device for user {user_id}, physical_device_id {physical_device_id}")
        except Exception as e:
            logger.error(f"Error in unregister_fcm_device for user {user_id}: {e}", exc_info=True)
            raise

    async def get_fcm_tokens_for_user(self, user_id: int) -> List[str]:
        try:
            tokens = await self._fcm_device_repo.get_tokens_by_user_id(user_id=user_id)
            logger.debug(f"Found {len(tokens)} FCM tokens for user_id {user_id}")
            return tokens
        except Exception as e:
            logger.error(f"Error getting FCM tokens for user_id {user_id}: {e}", exc_info=True)
            return []
