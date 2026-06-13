import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class SignalCreate(BaseModel):
    title: str
    description: Optional[str] = None
    symbol: str
    market: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    source: str = "manual"
    expires_at: Optional[datetime] = None

    @field_validator("market")
    @classmethod
    def validate_market(cls, v):
        allowed = {"forex", "crypto", "stocks", "indices", "commodities"}
        if v not in allowed:
            raise ValueError(f"market must be one of {allowed}")
        return v

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v):
        if v not in {"buy", "sell"}:
            raise ValueError("direction must be buy or sell")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v):
        allowed = {"manual", "tradingview", "strategy", "broker"}
        if v not in allowed:
            raise ValueError(f"source must be one of {allowed}")
        return v


class SignalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    current_price: Optional[float] = None
    status: Optional[str] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in {"open", "tp_hit", "sl_hit", "expired", "cancelled"}:
            raise ValueError("invalid status")
        return v


class SignalResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    symbol: str
    market: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    current_price: Optional[float] = None
    status: str
    source: str
    risk_reward_ratio: Optional[float] = None
    pips_risk: Optional[float] = None
    pips_reward: Optional[float] = None
    ai_score: Optional[int] = None
    ai_grade: Optional[str] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
