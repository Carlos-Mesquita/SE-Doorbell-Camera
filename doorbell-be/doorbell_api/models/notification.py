from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from doorbell_api.configs.db import Base, TimestampMixin

if TYPE_CHECKING:
    from .capture import Capture

class Notification(Base, TimestampMixin):
    __tablename__ = 'notifications'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()

    captures: Mapped[List['Capture']] = relationship(
        back_populates="notification",
        cascade="all, delete-orphan"
    )

