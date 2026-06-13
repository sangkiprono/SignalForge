import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_trader
from app.core.telegram import send_signal_alert
from app.core.websocket_manager import manager
from app.core.scoring import score_signal
from app.database import get_db
from app.models.signal import Signal
from app.models.signal_history import SignalHistory
from app.models.user import User
from app.schemas.signal import SignalCreate, SignalResponse, SignalUpdate

router = APIRouter(prefix="/signals", tags=["Signals"])


def calculate_rr(direction: str, entry: float, sl: float, tp: float):
    if direction == "buy":
        risk = entry - sl
        reward = tp - entry
    else:
        risk = sl - entry
        reward = entry - tp
    if risk <= 0:
        return None, None, None
    rr = round(reward / risk, 2)
    return rr, round(risk, 5), round(reward, 5)


async def get_symbol_win_rate(db: AsyncSession, symbol: str) -> float:
    tp = await db.execute(
        select(func.count(Signal.id)).where(Signal.symbol == symbol, Signal.status == "tp_hit")
    )
    sl = await db.execute(
        select(func.count(Signal.id)).where(Signal.symbol == symbol, Signal.status == "sl_hit")
    )
    tp_count = tp.scalar()
    sl_count = sl.scalar()
    closed = tp_count + sl_count
    return tp_count / closed if closed > 0 else 0.5


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
async def create_signal(
    signal_data: SignalCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trader),
):
    rr, pips_risk, pips_reward = calculate_rr(
        signal_data.direction,
        signal_data.entry_price,
        signal_data.stop_loss,
        signal_data.take_profit,
    )

    win_rate = await get_symbol_win_rate(db, signal_data.symbol.upper())

    from datetime import datetime, timezone
    ai_score, ai_grade = score_signal(
        direction=signal_data.direction,
        entry_price=signal_data.entry_price,
        stop_loss=signal_data.stop_loss,
        take_profit=signal_data.take_profit,
        market=signal_data.market,
        source=signal_data.source,
        created_at=datetime.now(timezone.utc),
        symbol_win_rate=win_rate,
    )

    signal = Signal(
        **signal_data.model_dump(),
        created_by=current_user.id,
        risk_reward_ratio=rr,
        pips_risk=pips_risk,
        pips_reward=pips_reward,
        ai_score=ai_score,
        ai_grade=ai_grade,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    history = SignalHistory(
        signal_id=signal.id,
        previous_status=None,
        new_status="open",
        notes=f"Signal created | AI Score: {ai_score} ({ai_grade})",
        changed_by=current_user.id,
    )
    db.add(history)
    await db.commit()

    await send_signal_alert(signal)
    await manager.broadcast({
        "type": "new_signal",
        "signal": {
            "id": str(signal.id),
            "title": signal.title,
            "symbol": signal.symbol,
            "market": signal.market,
            "direction": signal.direction,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "risk_reward_ratio": signal.risk_reward_ratio,
            "status": signal.status,
            "source": signal.source,
            "ai_score": signal.ai_score,
            "ai_grade": signal.ai_grade,
        }
    })
    return signal


@router.get("/", response_model=List[SignalResponse])
async def get_signals(
    market: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Signal)
    if market:
        query = query.where(Signal.market == market)
    if status:
        query = query.where(Signal.status == status)
    if symbol:
        query = query.where(Signal.symbol == symbol.upper())
    query = query.order_by(Signal.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/active", response_model=List[SignalResponse])
async def get_active_signals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Signal).where(Signal.status == "open").order_by(Signal.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return signal


@router.get("/{signal_id}/history")
async def get_signal_history(
    signal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SignalHistory)
        .where(SignalHistory.signal_id == signal_id)
        .order_by(SignalHistory.created_at.desc())
    )
    history = result.scalars().all()
    return [
        {
            "id": str(h.id),
            "signal_id": str(h.signal_id),
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "price_at_change": h.price_at_change,
            "notes": h.notes,
            "created_at": h.created_at,
        }
        for h in history
    ]


@router.put("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: uuid.UUID,
    updates: SignalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trader),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    if signal.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this signal")

    previous_status = signal.status
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(signal, field, value)

    if updates.status and updates.status != previous_status:
        history = SignalHistory(
            signal_id=signal.id,
            previous_status=previous_status,
            new_status=updates.status,
            price_at_change=updates.current_price,
            changed_by=current_user.id,
        )
        db.add(history)
        await send_signal_alert(signal)
        await manager.broadcast({
            "type": "signal_update",
            "signal_id": str(signal.id),
            "previous_status": previous_status,
            "new_status": updates.status,
        })

    await db.commit()
    await db.refresh(signal)
    return signal


@router.delete("/{signal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_signal(
    signal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_trader),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    if signal.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this signal")
    await db.delete(signal)
    await db.commit()
