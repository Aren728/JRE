import datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChartCalculation(Base):
    __tablename__ = "chart_calculations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    query_date: Mapped[datetime.date] = mapped_column(DateTime, nullable=False)
    query_time: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timezone: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )
