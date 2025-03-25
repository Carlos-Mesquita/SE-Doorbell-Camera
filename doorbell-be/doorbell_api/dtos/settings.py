from pydantic import BaseModel
from typing import Optional


class StopMotionConfig(BaseModel):
    interval: Optional[int] = None
    duration: Optional[int] = None


class CameraConfig(BaseModel):
    bitrate: Optional[int] = None
    stop_motion: Optional[StopMotionConfig] = None


class ColorConfig(BaseModel):
    r: Optional[int] = None
    g: Optional[int] = None
    b: Optional[int] = None


class ButtonConfig(BaseModel):
    debounce: Optional[int] = None
    polling_rate: Optional[int] = None


class MotionSensorConfig(BaseModel):
    debounce: Optional[int] = None
    polling_rate: Optional[int] = None


class SettingsDTO(BaseModel):
    button: Optional[ButtonConfig] = None
    motion_sensor: Optional[MotionSensorConfig] = None
    camera: Optional[CameraConfig] = None
    color: Optional[ColorConfig] = None
