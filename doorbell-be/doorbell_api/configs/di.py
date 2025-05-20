from asyncio import Queue

from dependency_injector import providers, containers
from ..configs.db import scoped_session


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

        self._container.db_session = providers.Factory(
            scoped_session
        )
        self._container.token_repo = providers.Factory(
            TokenRepository, db_session=self._container.db_session, config=self._container.config
        )
        self._container.user_repo = providers.Factory(
            UserRepository, db_session=self._container.db_session
        )
        self._container.capture_repo = providers.Factory(
            CaptureRepository, db_session=self._container.db_session
        )
        self._container.settings_repo = providers.Factory(
            SettingsRepository, db_session=self._container.db_session
        )
        self._container.notification_repo = providers.Factory(
            NotificationRepository, db_session=self._container.db_session
        )
        self._container.fcm_device_repo = providers.Factory(
            FCMDeviceRepository, db_session=self._container.db_session
        )

    def _setup_services(self):
        from ..services.impl import (
            AuthService, TokenService, CaptureService,
            SettingsService, NotificationService,
            MessageHandler, DeviceService
        )

        self._container.token_service = providers.Factory(
            TokenService, token_repo=self._container.token_repo
        )

        self._container.capture_service = providers.Factory(
            CaptureService, mapper=self._container.capture_mapper, repo=self._container.capture_repo
        )
        self._container.settings_service = providers.Factory(
            SettingsService, mapper=self._container.settings_mapper, repo=self._container.settings_repo
        )
        self._container.device_service = providers.Factory(
            DeviceService, fcm_device_repo=self._container.fcm_device_repo
        )

        self._container.notification_service = providers.Factory(
            NotificationService,
            mapper=self._container.notification_mapper,
            repo=self._container.notification_repo,
            device_service=self._container.device_service
        )

        self._container.message_handler = providers.Factory(
            MessageHandler,
            notification_service=self._container.notification_service,
            capture_service=self._container.capture_service,
            notification_repo=self._container.notification_repo,
            captures_base_dir='/opt/captures'
        )

        self._container.auth_service = providers.Factory(
            AuthService,
            token_service=self._container.token_service,
            user_repo=self._container.user_repo,
            config=self._container.config
        )

    def _setup_controllers(self):
        from ..controllers.impl import (
            AuthController, CaptureController,
            SettingsController, NotificationController,
            WebsocketController
        )

        self._container.auth_controller = providers.Factory(
            AuthController, service=self._container.auth_service
        )
        self._container.capture_controller = providers.Factory(
            CaptureController, service=self._container.capture_service
        )
        self._container.settings_controller = providers.Factory(
            SettingsController, service=self._container.settings_service
        )
        self._container.notification_controller = providers.Factory(
            NotificationController, service=self._container.notification_service
        )

        self._container.ws_controller = providers.Factory(
            WebsocketController,
            auth_service=self._container.auth_service,
            message_handler=self._container.message_handler,
            signaling_service=self._container.signaling_service
        )
