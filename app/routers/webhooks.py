from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.signal import Signal
from app.models.signal_history import SignalHistory
from app.schemas.signal import SignalResponse

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/tradingview", response_model=SignalResponse, status_code=201)
async def tradingview_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_secret: str = Header(None),
):
    if x_webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    required = ["symbol", "direction", "entry_price", "stop_loss", "take_profit"]
    for field in required:
        if field not in data:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    direction = str(data["direction"]).lower()
    if direction not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="direction must be buy or sell")

    entry = float(data["entry_price"])
    sl = float(data["stop_loss"])
    tp = float(data["take_profit"])

    if direction == "buy":
        risk = entry - sl
        reward = tp - entry
    else:
        risk = sl - entry
        reward = entry - tp

    rr = round(reward / risk, 2) if risk > 0 else None

    signal = Signal(
        title=data.get("title", f"{data['symbol']} {direction.upper()} - TradingView"),
        description=data.get("description", "Signal from TradingView webhook"),
        symbol=str(data["symbol"]).upper(),
        market=data.get("market", "forex"),
        direction=direction,
        entry_price=entry,
        stop_loss=sl,
        take_profit=tp,
        source="tradingview",
        risk_reward_ratio=rr,
        pips_risk=round(risk, 5) if risk > 0 else None,
        pips_reward=round(reward, 5) if risk > 0 else None,
        created_by=None,
    )
    db.add(signal)
    await db.flush()

    history = SignalHistory(
        signal_id=signal.id,
        previous_status=None,
        new_status="open",
        notes="Created via TradingView webhook",
    )
    db.add(history)
    await db.commit()
    await db.refresh(signal)
    return signal
