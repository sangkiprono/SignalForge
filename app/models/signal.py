import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    market: Mapped[str] = mapped_column(
        Enum("forex", "crypto", "stocks", "indices", "commodities", name="market_type"), nullable=False
    )
    direction: Mapped[str] = mapped_column(
        Enum("buy", "sell", name="signal_direction"), nullable=False
    )

    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    status: Mapped[str] = mapped_column(
        Enum("open", "tp_hit", "sl_hit", "expired", "cancelled", name="signal_status"),
        default="open", nullable=False, index=True,
    )
    source: Mapped[str] = mapped_column(
        Enum("manual", "tradingview", "strategy", "broker", name="signal_source"),
        default="manual", nullable=False,
    )

    risk_reward_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pips_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    pips_reward: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ai_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    creator: Mapped[Optional["User"]] = relationship("User", backref="signals")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Signal {self.symbol} {self.direction} {self.status}>"
