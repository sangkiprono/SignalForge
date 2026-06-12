from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.signal import Signal
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = await db.execute(select(func.count(Signal.id)))
    total_signals = total.scalar()

    open_result = await db.execute(select(func.count(Signal.id)).where(Signal.status == "open"))
    open_signals = open_result.scalar()

    tp_result = await db.execute(select(func.count(Signal.id)).where(Signal.status == "tp_hit"))
    tp_signals = tp_result.scalar()

    sl_result = await db.execute(select(func.count(Signal.id)).where(Signal.status == "sl_hit"))
    sl_signals = sl_result.scalar()

    closed = tp_signals + sl_signals
    win_rate = round((tp_signals / closed) * 100, 2) if closed > 0 else 0
    loss_rate = round((sl_signals / closed) * 100, 2) if closed > 0 else 0
    profit_factor = round(tp_signals / sl_signals, 2) if sl_signals > 0 else None

    return {
        "total_signals": total_signals,
        "open_signals": open_signals,
        "tp_hit": tp_signals,
        "sl_hit": sl_signals,
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "profit_factor": profit_factor,
    }


@router.get("/by-market")
async def get_by_market(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Signal.market, func.count(Signal.id)).group_by(Signal.market)
    )
    rows = result.all()
    return [{"market": row[0], "count": row[1]} for row in rows]


@router.get("/by-symbol")
async def get_by_symbol(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Signal.symbol, func.count(Signal.id)).group_by(Signal.symbol).order_by(func.count(Signal.id).desc())
    )
    rows = result.all()
    return [{"symbol": row[0], "count": row[1]} for row in rows]


@router.get("/win-rate-by-market")
async def get_win_rate_by_market(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    markets = ["forex", "crypto", "stocks", "indices", "commodities"]
    result = []

    for market in markets:
        tp = await db.execute(
            select(func.count(Signal.id)).where(Signal.market == market, Signal.status == "tp_hit")
        )
        sl = await db.execute(
            select(func.count(Signal.id)).where(Signal.market == market, Signal.status == "sl_hit")
        )
        tp_count = tp.scalar()
        sl_count = sl.scalar()
        closed = tp_count + sl_count
        win_rate = round((tp_count / closed) * 100, 2) if closed > 0 else 0

        result.append({
            "market": market,
            "tp_hit": tp_count,
            "sl_hit": sl_count,
            "win_rate": win_rate,
        })

    return result
