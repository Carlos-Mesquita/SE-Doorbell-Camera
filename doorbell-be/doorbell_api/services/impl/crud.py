from ...dtos import CaptureDTO, NotificationDTO, SettingsDTO
from ...models import Capture, Notification, Settings
from ...services import ICaptureService, INotificationService, ISettingsService
from ...repositories import (
    ICaptureRepository, INotificationRepository, ISettingsRepository
)
from ...mappers import IMapper

from .base import BaseService


class CaptureService(BaseService[CaptureDTO, Capture], ICaptureService):
    def __init__(self, mapper: IMapper[CaptureDTO, Capture], repo: ICaptureRepository):
        super().__init__(mapper, repo)
        self._repo = repo


class SettingsService(BaseService[SettingsDTO, Settings], ISettingsService):
    def __init__(self, mapper: IMapper[SettingsDTO, Settings], repo: ISettingsRepository):
        super().__init__(mapper, repo)
        self._repo = repo
