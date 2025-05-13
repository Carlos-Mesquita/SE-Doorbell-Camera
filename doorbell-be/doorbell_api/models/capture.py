from doorbell_api.configs.db import Base, TimestampMixin

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .notification import Notification

class Capture(Base, TimestampMixin):
    __tablename__ = 'captures'

    id: Mapped[int] = mapped_column(primary_key=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey("notifications.id"))
    path: Mapped[str] = mapped_column()

    notification: Mapped[Notification] = relationship("Notification", back_populates="captures")
