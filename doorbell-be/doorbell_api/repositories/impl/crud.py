
from doorbell_api.models import Capture, Notification, Settings
from doorbell_api.repositories import (
    ICaptureRepository, INotificationRepository, ISettingsRepository
)
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseRepository


class CaptureRepository(BaseRepository[Capture], ICaptureRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Capture, db_session)


class NotificationRepository(BaseRepository[Notification], INotificationRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Notification, db_session)

class SettingsRepository(BaseRepository[Settings], ISettingsRepository):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Settings, db_session)
