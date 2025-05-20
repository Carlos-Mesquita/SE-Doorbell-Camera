from typing import Optional

from doorbell_api.models import Capture, Notification, Settings
from doorbell_api.repositories import (
    ICaptureRepository, INotificationRepository, ISettingsRepository
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Select
from .base import BaseRepository


class CaptureRepository(BaseRepository[Capture], ICaptureRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Capture, db_session)


class NotificationRepository(BaseRepository[Notification], INotificationRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Notification, db_session)

    async def find_by_rpi_event_id(self, rpi_event_id: str, user_id: Optional[str] = None) -> Optional[Notification]:
        stmt = Select(Notification).where(Notification.rpi_event_id == rpi_event_id)
        if user_id:
            stmt = stmt.where(Notification.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

class SettingsRepository(BaseRepository[Settings], ISettingsRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Settings, db_session)
