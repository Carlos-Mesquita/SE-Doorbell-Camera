from typing import List, TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer
from ..configs.db import Base, TimestampMixin

if TYPE_CHECKING:
    from .capture import Capture


class Notification(Base, TimestampMixin):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()

    rpi_event_id: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    type_str: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)

    captures: Mapped[List['Capture']] = relationship(
        "Capture",
        back_populates="notification",
        cascade="all, delete-orphan"
    )
