import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_trader
from app.core.telegram import send_signal_alert
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

    signal = Signal(
        **signal_data.model_dump(),
        created_by=current_user.id,
        risk_reward_ratio=rr,
        pips_risk=pips_risk,
        pips_reward=pips_reward,
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)

    history = SignalHistory(
        signal_id=signal.id,
        previous_status=None,
        new_status="open",
        notes="Signal created",
        changed_by=current_user.id,
    )
    db.add(history)
    await db.commit()

    await send_signal_alert(signal)
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
