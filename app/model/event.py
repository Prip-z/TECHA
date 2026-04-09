from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EventType(str, enum.Enum):
    default = "default"
    tournament = "tournament"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    type: Mapped[EventType] = mapped_column(
        Enum(EventType, name="event_type"),
        nullable=False,
        default=EventType.default,
        server_default=EventType.default.value,
    )
    price_per_game: Mapped[float] = mapped_column(Float, nullable=False)
