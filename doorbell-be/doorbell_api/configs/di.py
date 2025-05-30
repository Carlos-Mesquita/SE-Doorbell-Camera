from dependency_injector import providers, containers
from ..configs.db import DB, set_db


class DependencyInjector:

    def __init__(self):
        self._container = containers.DynamicContainer()

    def inject(self):
        self._setup_configs()
        self._setup_mappers()
        self._setup_repositories()
        self._setup_shared_instances()
        self._setup_services()
        self._setup_controllers()
        self._container.wire(
            packages=["doorbell_api"]
        )
        return self

    def _setup_configs(self):
        self._container.config = providers.Configuration()
        self._container.config.jwt.algorithm.from_env("JWT_ALGORITHM", required=True)

        self._container.config.jwt.refresh.key.from_env("JWT_REFRESH_SECRET_KEY", required=True)
        self._container.config.jwt.refresh.expires.from_env("JWT_REFRESH_TOKEN_EXPIRE", required=True)

        self._container.config.jwt.access.key.from_env("JWT_ACCESS_SECRET_KEY", required=True)
        self._container.config.jwt.access.expires.from_env("JWT_ACCESS_TOKEN_EXPIRE", required=True)

        self._container.config.capture_dir.from_env("CAPTURE_DIR", required=True)

    def _setup_shared_instances(self):
        from ..services.impl import WebRTCSignalingService
        self._container.signaling_service = providers.Singleton(WebRTCSignalingService)

    def _setup_mappers(self):
        from ..mappers.impl import (
            CaptureMapper, NotificationMapper, SettingsMapper
        )
        self._container.capture_mapper = providers.Singleton(CaptureMapper)
        self._container.notification_mapper = providers.Singleton(NotificationMapper)
        self._container.settings_mapper = providers.Singleton(SettingsMapper)

    def _setup_repositories(self):
        from ..repositories.impl import (
            TokenRepository, UserRepository, CaptureRepository,
            SettingsRepository, NotificationRepository, FCMDeviceRepository
        )

        db = DB()
        set_db(db)
        self._container.db = providers.Object(db)
        self._container.token_repo = providers.Factory(TokenRepository)
        self._container.user_repo = providers.Factory(UserRepository)
        self._container.capture_repo = providers.Factory(CaptureRepository)
        self._container.settings_repo = providers.Factory(SettingsRepository)
        self._container.notification_repo = providers.Factory(NotificationRepository)
        self._container.fcm_device_repo = providers.Factory(FCMDeviceRepository)

    def _setup_services(self):
        from ..services.impl import (
            AuthService, TokenService, CaptureService,
            SettingsService, NotificationService,
            MessageHandler, DeviceService
        )
        self._container.token_service = providers.Factory(TokenService)
        self._container.capture_service = providers.Factory(CaptureService)
        self._container.settings_service = providers.Factory(SettingsService)
        self._container.device_service = providers.Factory(DeviceService)
        self._container.notification_service = providers.Factory(NotificationService)
        self._container.message_handler = providers.Factory(MessageHandler)
        self._container.auth_service = providers.Factory(AuthService)

    def _setup_controllers(self):
        from ..controllers.impl import (
            AuthController, CaptureController,
            SettingsController, NotificationController,
            WebsocketController
        )
        self._container.auth_controller = providers.Factory(AuthController)
        self._container.capture_controller = providers.Factory(CaptureController)
        self._container.settings_controller = providers.Factory(SettingsController)
        self._container.notification_controller = providers.Factory(NotificationController)
        self._container.ws_controller = providers.Factory(WebsocketController)
