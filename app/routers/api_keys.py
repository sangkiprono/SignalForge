import hashlib
import secrets
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


def generate_api_key():
    raw = secrets.token_urlsafe(32)
    full_key = f"sf_{raw}"
    prefix = full_key[:8]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, prefix, key_hash


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    full_key, prefix, key_hash = generate_api_key()

    api_key = APIKey(
        user_id=current_user.id,
        name=name,
        key_hash=key_hash,
        prefix=prefix,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "id": str(api_key.id),
        "name": api_key.name,
        "prefix": api_key.prefix,
        "key": full_key,
        "created_at": api_key.created_at,
        "message": "Save this key - it will not be shown again.",
    }


@router.get("/", response_model=List[dict])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id)
    )
    keys = result.scalars().all()
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "prefix": k.prefix,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at,
            "created_at": k.created_at,
        }
        for k in keys
    ]


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    key = result.scalar_one_or_none()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    await db.delete(key)
    await db.commit()
