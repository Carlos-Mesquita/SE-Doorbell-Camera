from .base import BaseController
from doorbell_api.dtos import NotificationDTO, CaptureDTO, SettingsDTO
from doorbell_api.controllers import (
    INotificationController, ICaptureController, ISettingsController
)
from doorbell_api.services import INotificationService, ICaptureService, ISettingsService

class NotificationController(BaseController[NotificationDTO], INotificationController):
    def __init__(self, service: INotificationService):
        super().__init__(service)


class CaptureController(BaseController[CaptureDTO], ICaptureController):
    def __init__(self, service: ICaptureService):
        super().__init__(service)

class SettingsController(BaseController[SettingsDTO], ISettingsController):
    def __init__(self, service: ISettingsService):
        super().__init__(service)
