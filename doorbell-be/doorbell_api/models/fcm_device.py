import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..configs.db import Base, TimestampMixin
from .user import User


class FCMDevice(Base, TimestampMixin):
    __tablename__ = "fcm_devices"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user: Mapped["User"] = relationship()

    fcm_token: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    physical_device_id: Mapped[str] = mapped_column(String, index=True, nullable=False)

    device_type: Mapped[Optional[str]] = mapped_column(String(50))
    app_version: Mapped[Optional[str]] = mapped_column(String(50))
    last_seen_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.now())
