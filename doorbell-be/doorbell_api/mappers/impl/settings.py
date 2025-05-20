from typing import Dict, Any
from ...models import Settings
from ...dtos.settings import (
    SettingsDTO, ButtonConfig, MotionSensorConfig,
    CameraConfig, ColorConfig, StopMotionConfig
)

from .base import Mapper


class SettingsMapper(Mapper[SettingsDTO, Settings]):
    def __init__(self):
        super().__init__(
            orm_model=Settings,
            dto_model=SettingsDTO,
            field_mapping={},
            exclude_dto_keys=set(),
            exclude_orm_keys=set()
        )

    def to_dto(self, orm_model: Settings, exclusions=None) -> SettingsDTO:
        return SettingsDTO(
            button=ButtonConfig(
                debounce=orm_model.button_debounce,
                polling_rate=orm_model.button_polling_rate
            ),
            motion_sensor=MotionSensorConfig(
                debounce=orm_model.motion_sensor_debounce,
                polling_rate=orm_model.motion_sensor_polling_rate
            ),
            camera=CameraConfig(
                bitrate=orm_model.camera_bitrate,
                stop_motion=StopMotionConfig(
                    interval=orm_model.camera_stop_motion_interval,
                    duration=orm_model.camera_stop_motion_duration
                )
            ),
            color=ColorConfig(
                r=orm_model.color_r,
                g=orm_model.color_g,
                b=orm_model.color_b
            )
        )

    def _create_new_model(self, dto: SettingsDTO) -> Settings:
        settings = Settings()
        return self._update_existing_model(dto, settings)

    def _update_existing_model(self, dto: SettingsDTO, existing_model: Settings) -> Settings:
        if dto.button:
            if dto.button.debounce is not None:
                existing_model.button_debounce = dto.button.debounce
            if dto.button.polling_rate is not None:
                existing_model.button_polling_rate = dto.button.polling_rate

        if dto.motion_sensor:
            if dto.motion_sensor.debounce is not None:
                existing_model.motion_sensor_debounce = dto.motion_sensor.debounce
            if dto.motion_sensor.polling_rate is not None:
                existing_model.motion_sensor_polling_rate = dto.motion_sensor.polling_rate

        if dto.camera:
            if dto.camera.bitrate is not None:
                existing_model.camera_bitrate = dto.camera.bitrate
            if dto.camera.stop_motion:
                if dto.camera.stop_motion.interval is not None:
                    existing_model.camera_stop_motion_interval = dto.camera.stop_motion.interval
                if dto.camera.stop_motion.duration is not None:
                    existing_model.camera_stop_motion_duration = dto.camera.stop_motion.duration

        if dto.color:
            if dto.color.r is not None:
                existing_model.color_r = dto.color.r
            if dto.color.g is not None:
                existing_model.color_g = dto.color.g
            if dto.color.b is not None:
                existing_model.color_b = dto.color.b

        return existing_model

    def dto_kwargs(self, dto: SettingsDTO) -> Dict[str, Any]:
        kwargs = {}

        if dto.button:
            if dto.button.debounce is not None:
                kwargs['button_debounce'] = dto.button.debounce
            if dto.button.polling_rate is not None:
                kwargs['button_polling_rate'] = dto.button.polling_rate

        if dto.motion_sensor:
            if dto.motion_sensor.debounce is not None:
                kwargs['motion_sensor_debounce'] = dto.motion_sensor.debounce
            if dto.motion_sensor.polling_rate is not None:
                kwargs['motion_sensor_polling_rate'] = dto.motion_sensor.polling_rate

        if dto.camera:
            if dto.camera.bitrate is not None:
                kwargs['camera_bitrate'] = dto.camera.bitrate
            if dto.camera.stop_motion:
                if dto.camera.stop_motion.interval is not None:
                    kwargs['camera_stop_motion_interval'] = dto.camera.stop_motion.interval
                if dto.camera.stop_motion.duration is not None:
                    kwargs['camera_stop_motion_duration'] = dto.camera.stop_motion.duration

        if dto.color:
            if dto.color.r is not None:
                kwargs['color_r'] = dto.color.r
            if dto.color.g is not None:
                kwargs['color_g'] = dto.color.g
            if dto.color.b is not None:
                kwargs['color_b'] = dto.color.b

        return kwargs
