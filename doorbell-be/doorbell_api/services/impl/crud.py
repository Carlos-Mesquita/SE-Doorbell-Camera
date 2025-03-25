from doorbell_api.dtos import CaptureDTO, NotificationDTO, SettingsDTO
from doorbell_api.models import Capture, Notification, Settings
from doorbell_api.services import ICaptureService, INotificationService, ISettingsService
from doorbell_api.repositories import (
    ICaptureRepository, INotificationRepository, ISettingsRepository
)
from doorbell_api.mappers import IMapper

from .base import BaseService


class CaptureService(BaseService[CaptureDTO, Capture], ICaptureService):
    def __init__(self, mapper: IMapper[CaptureDTO, Capture], repo: ICaptureRepository):
        super().__init__(mapper, repo)
        self._repo = repo

class NotificationService(BaseService[NotificationDTO, Notification], INotificationService):
    def __init__(self, mapper: IMapper[NotificationDTO, Notification], repo: INotificationRepository):
        super().__init__(mapper, repo)
        self._repo = repo

class SettingsService(BaseService[SettingsDTO, Settings], ISettingsService):
    def __init__(self, mapper: IMapper[SettingsDTO, Settings], repo: ISettingsRepository):
        super().__init__(mapper, repo)
        self._repo = repo
