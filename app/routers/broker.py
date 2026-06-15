from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.broker import get_account_info, get_open_positions, place_trade
from app.core.dependencies import require_trader
from app.models.user import User

router = APIRouter(prefix="/broker", tags=["Broker"])


class TradeRequest(BaseModel):
    symbol: str
    direction: str
    volume: float = 0.01
    stop_loss: float
    take_profit: float
    comment: str = "SignalForge"


@router.get("/account")
async def account_info(current_user: User = Depends(require_trader)):
    result = await get_account_info()
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@router.post("/trade")
async def execute_trade(
    trade: TradeRequest,
    current_user: User = Depends(require_trader),
):
    if trade.direction not in {"buy", "sell"}:
        raise HTTPException(status_code=400, detail="direction must be buy or sell")
    result = await place_trade(
        symbol=trade.symbol,
        direction=trade.direction,
        volume=trade.volume,
        stop_loss=trade.stop_loss,
        take_profit=trade.take_profit,
        comment=trade.comment,
    )
    if "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result


@router.get("/positions")
async def open_positions(current_user: User = Depends(require_trader)):
    result = await get_open_positions()
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=503, detail=result["error"])
    return result
