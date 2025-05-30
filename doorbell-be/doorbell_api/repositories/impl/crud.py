from datetime import timedelta, datetime
from logging import getLogger
from typing import Optional, Any

from doorbell_api.models import Capture, Notification, Settings
from doorbell_api.repositories import (
    ICaptureRepository, INotificationRepository, ISettingsRepository
)
from sqlalchemy import Select
from .base import BaseRepository


class CaptureRepository(BaseRepository[Capture], ICaptureRepository):
    def __init__(self):
        super().__init__(Capture)


class NotificationRepository(BaseRepository[Notification], INotificationRepository):
    def __init__(self):
        super().__init__(Notification)
        self._logger = getLogger(__name__)

    async def find_by_rpi_event_id(self, rpi_event_id: str, user_id: Optional[str] = None) -> Optional[Notification]:
        stmt = Select(Notification).where(Notification.rpi_event_id == rpi_event_id)
        if user_id:
            stmt = stmt.where(Notification.user_id == int(user_id))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_rate_limited(self, user_id: str, rate_limit = 1):
        filter_conditions = {
            "user_id": int(user_id),
            "type_str": "motion_detected"
        }

        args = {
            "page": 1,
            "page_size": 1,
            "sort_by": "created_at",
            "sort_order": "desc",
            "filter_by": filter_conditions
        }
        results = await super().get_all(**args)
        if not results:
            return True
        last_notification = results[0]
        last_notification_time = last_notification.created_at
        time_since_last_notification = datetime.now() - last_notification_time
        required_interval = timedelta(minutes=rate_limit)

        self._logger.debug(
            f"Last motion notification for user {user_id} was at {last_notification_time}. "
            f"Time since: {time_since_last_notification}, Required: {required_interval}"
        )
        return time_since_last_notification >= required_interval


class SettingsRepository(BaseRepository[Settings], ISettingsRepository):
    def __init__(self):
        super().__init__(Settings)
