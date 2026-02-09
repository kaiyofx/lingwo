from datetime import datetime
from sqlalchemy import String, DateTime, Float, JSON, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    target_percent: Mapped[int] = mapped_column(Integer, default=70)  # 0–100, целевой процент выполнения
    auto_save_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    auto_save_interval_sec: Mapped[int] = mapped_column(Integer, default=30)


class Essay(Base):
    __tablename__ = "essays"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    essay_type: Mapped[str] = mapped_column(String(16))
    theme: Mapped[str] = mapped_column(String(512))
    text: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_score: Mapped[float] = mapped_column(Float)  # сырые баллы (сумма по критериям)
    total_score_per: Mapped[float | None] = mapped_column(Float, nullable=True)  # доля от максимума 0–1
    max_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    criteries: Mapped[dict] = mapped_column(JSON, default=dict)
    common_mistakes: Mapped[list] = mapped_column(JSON, default=list)
