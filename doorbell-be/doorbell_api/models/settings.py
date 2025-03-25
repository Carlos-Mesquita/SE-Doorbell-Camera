from sqlalchemy.orm import Mapped, mapped_column

from doorbell_api.configs.db import Base, TimestampMixin


class Settings(Base, TimestampMixin):
    __tablename__ = 'settings'

    id: Mapped[int] = mapped_column(primary_key=True)

    button_debounce: Mapped[int] = mapped_column()
    button_polling_rate: Mapped[int] = mapped_column()

    motion_sensor_debounce: Mapped[int] = mapped_column()
    motion_sensor_polling_rate: Mapped[int] = mapped_column()

    camera_bitrate: Mapped[int] = mapped_column()
    camera_stop_motion_interval: Mapped[int] = mapped_column()
    camera_stop_motion_duration: Mapped[int] = mapped_column()

    color_r: Mapped[int] = mapped_column()
    color_g: Mapped[int] = mapped_column()
    color_b: Mapped[int] = mapped_column()
