from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_admin
from app.database import get_db
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

TIER_LIMITS = {
    "free": {"signals_limit": 10, "api_calls_limit": 100},
    "premium": {"signals_limit": 500, "api_calls_limit": 10000},
    "enterprise": {"signals_limit": 999999, "api_calls_limit": 999999},
}


@router.get("/me")
async def get_my_subscription(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()

    if not sub:
        return {
            "tier": "free",
            "is_active": True,
            "signals_limit": 10,
            "api_calls_limit": 100,
            "signals_used": 0,
            "api_calls_used": 0,
            "expires_at": None,
        }

    return {
        "tier": sub.tier,
        "is_active": sub.is_active,
        "signals_limit": sub.signals_limit,
        "api_calls_limit": sub.api_calls_limit,
        "signals_used": sub.signals_used,
        "api_calls_used": sub.api_calls_used,
        "expires_at": sub.expires_at,
        "started_at": sub.started_at,
    }


@router.post("/upgrade")
async def upgrade_subscription(
    tier: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if tier not in TIER_LIMITS:
        raise HTTPException(status_code=400, detail="Invalid tier. Choose: free, premium, enterprise")

    result = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id)
    )
    sub = result.scalar_one_or_none()
    limits = TIER_LIMITS[tier]

    if sub:
        sub.tier = tier
        sub.signals_limit = limits["signals_limit"]
        sub.api_calls_limit = limits["api_calls_limit"]
        sub.signals_used = 0
        sub.api_calls_used = 0
    else:
        sub = Subscription(
            user_id=current_user.id,
            tier=tier,
            signals_limit=limits["signals_limit"],
            api_calls_limit=limits["api_calls_limit"],
        )
        db.add(sub)

    await db.commit()
    await db.refresh(sub)

    return {
        "message": f"Upgraded to {tier}",
        "tier": sub.tier,
        "signals_limit": sub.signals_limit,
        "api_calls_limit": sub.api_calls_limit,
    }


@router.get("/all")
async def get_all_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(Subscription))
    subs = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "user_id": str(s.user_id),
            "tier": s.tier,
            "is_active": s.is_active,
            "signals_used": s.signals_used,
            "signals_limit": s.signals_limit,
            "started_at": s.started_at,
        }
        for s in subs
    ]
