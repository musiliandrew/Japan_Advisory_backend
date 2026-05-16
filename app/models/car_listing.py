from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class CarListing(Base):
    __tablename__ = 'car_listings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    make: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    year: Mapped[int | None] = mapped_column(Integer)
    mileage_km: Mapped[str | None] = mapped_column(Text)
    engine_cc: Mapped[str | None] = mapped_column(Text)
    fuel_type: Mapped[str | None] = mapped_column(Text)
    transmission: Mapped[str | None] = mapped_column(Text)
    body_type: Mapped[str | None] = mapped_column(Text)
    drive_type: Mapped[str | None] = mapped_column(Text)
    stock_id: Mapped[str | None] = mapped_column(Text)
    price_usd: Mapped[int | None] = mapped_column(BigInteger)
    total_price_usd: Mapped[int | None] = mapped_column(BigInteger)
    url: Mapped[str | None] = mapped_column(Text)
    source_platform: Mapped[str | None] = mapped_column(Text)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
