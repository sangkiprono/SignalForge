from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.database import get_db
from app.models.signal import Signal
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_users = await db.execute(select(func.count(User.id)))
    total_signals = await db.execute(select(func.count(Signal.id)))
    active_signals = await db.execute(select(func.count(Signal.id)).where(Signal.status == "open"))
    total_subs = await db.execute(select(func.count(Subscription.id)))
    premium_subs = await db.execute(select(func.count(Subscription.id)).where(Subscription.tier == "premium"))

    return {
        "total_users": total_users.scalar(),
        "total_signals": total_signals.scalar(),
        "active_signals": active_signals.scalar(),
        "total_subscriptions": total_subs.scalar(),
        "premium_subscriptions": premium_subs.scalar(),
    }


@router.get("/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if role not in {"admin", "trader", "client"}:
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = role
    await db.commit()
    return {"message": f"Role updated to {role}", "user_id": user_id}


@router.put("/users/{user_id}/toggle")
async def toggle_user_active(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = not user.is_active
    await db.commit()
    return {"message": f"User {'activated' if user.is_active else 'deactivated'}", "is_active": user.is_active}


@router.get("/signals")
async def get_all_signals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Signal).order_by(Signal.created_at.desc()))
    signals = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "title": s.title,
            "symbol": s.symbol,
            "market": s.market,
            "direction": s.direction,
            "status": s.status,
            "source": s.source,
            "created_by": str(s.created_by) if s.created_by else None,
            "created_at": s.created_at,
        }
        for s in signals
    ]


@router.delete("/signals/{signal_id}")
async def admin_delete_signal(
    signal_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Signal).where(Signal.id == signal_id))
    signal = result.scalar_one_or_none()
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    await db.delete(signal)
    await db.commit()
    return {"message": "Signal deleted"}
