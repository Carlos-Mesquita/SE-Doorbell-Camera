from typing import Optional, List, Type

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime

from doorbell_api.models import FCMDevice
from doorbell_api.repositories import IFCMDeviceRepository
from doorbell_api.repositories.impl.base import BaseRepository


class FCMDeviceRepository(BaseRepository[FCMDevice], IFCMDeviceRepository):

    def __init__(self, session: AsyncSession, db_session: AsyncSession):
        super().__init__(FCMDevice, db_session)
        self.session = session

    async def get_by_user_and_physical_id(self, user_id: int, physical_device_id: str) -> Optional[FCMDevice]:
        stmt = select(FCMDevice).where(
            FCMDevice.user_id == user_id, FCMDevice.physical_device_id == physical_device_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_fcm_device(self, user_id: int, fcm_token: str, physical_device_id: str, device_type: Optional[str], app_version: Optional[str]) -> FCMDevice:
        device = FCMDevice(
            user_id=user_id, fcm_token=fcm_token, physical_device_id=physical_device_id,
            device_type=device_type, app_version=app_version, last_seen_at=datetime.now()
        )
        self.session.add(device)
        await self.session.flush()
        return device

    async def update_fcm_device_token(self, device_id: int, new_fcm_token: str, new_app_version: Optional[str]) -> Optional[FCMDevice]:
        stmt = update(FCMDevice).where(FCMDevice.id == device_id).values(
            fcm_token=new_fcm_token, app_version=new_app_version, last_seen_at=datetime.now(), updated_at=datetime.now()
        ).returning(FCMDevice)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def delete_by_user_and_physical_id(self, user_id: int, physical_device_id: str) -> bool:
        stmt = delete(FCMDevice).where(FCMDevice.user_id == user_id, FCMDevice.physical_device_id == physical_device_id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0


    async def get_tokens_by_user_id(self, user_id: int) -> List[str]:
        stmt = select(FCMDevice.fcm_token).where(FCMDevice.user_id == user_id)
        result = await self.session.execute(stmt)
        return [row[0] for row in result.all()]
