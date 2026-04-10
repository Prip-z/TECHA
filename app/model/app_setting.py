from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    value: Mapped[str] = mapped_column(String(4000), nullable=False)
