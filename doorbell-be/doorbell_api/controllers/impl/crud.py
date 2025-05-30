import time
from .base import BaseController
from ...dtos import NotificationDTO, CaptureDTO, SettingsDTO
from ...controllers import (
    INotificationController, ICaptureController, ISettingsController
)
from ...services import INotificationService, ICaptureService, ISettingsService
from fastapi.responses import StreamingResponse
from dependency_injector.wiring import Provide, inject


class NotificationController(BaseController[NotificationDTO], INotificationController):
    @inject
    def __init__(self, service: INotificationService = Provide['notification_service']):
        super().__init__(service)


class CaptureController(BaseController[CaptureDTO], ICaptureController):
    @inject
    def __init__(self, service: ICaptureService = Provide['capture_service']):
        super().__init__(service)
        self._service = service

    async def generate_cap_video(self, paths: list[str]):
        video_gen = self._service.generate_video(paths)

        return StreamingResponse(
            video_gen,
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename=stop_motion_{int(time.time())}.mp4"
            }
        )


class SettingsController(BaseController[SettingsDTO], ISettingsController):
    @inject
    def __init__(self, service: ISettingsService = Provide['settings_service']):
        super().__init__(service)
