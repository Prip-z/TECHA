from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    nick: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    social_link: Mapped[str | None] = mapped_column(String(1000), nullable=True)
