from fastapi import APIRouter, Depends
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

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
    return {
        "login": 52920919,
        "name": "Bryan Sang",
        "server": "ICMarketsKE-Demo",
        "currency": "USD",
        "balance": 10000.00,
        "equity": 10245.50,
        "margin": 120.00,
        "freeMargin": 10125.50,
        "marginLevel": 8537.92,
        "openPositionsCount": 2,
        "broker": "IC Markets KE",
        "type": "ACCOUNT_TRADE_MODE_DEMO",
        "platform": "mt5",
    }


@router.post("/trade")
async def execute_trade(
    trade: TradeRequest,
    current_user: User = Depends(require_trader),
):
    return {
        "orderId": str(uuid.uuid4()),
        "symbol": trade.symbol.upper(),
        "direction": trade.direction,
        "volume": trade.volume,
        "stopLoss": trade.stop_loss,
        "takeProfit": trade.take_profit,
        "comment": trade.comment,
        "status": "ORDER_STATE_FILLED",
        "executedAt": datetime.now(timezone.utc).isoformat(),
        "message": "Trade executed successfully (demo mode)",
    }


@router.get("/positions")
async def open_positions(current_user: User = Depends(require_trader)):
    return [
        {
            "id": "1001",
            "symbol": "EURUSD",
            "direction": "buy",
            "volume": 0.01,
            "openPrice": 1.0850,
            "currentPrice": 1.0875,
            "stopLoss": 1.0800,
            "takeProfit": 1.0950,
            "profit": 2.50,
            "openedAt": "2026-06-15T08:00:00Z",
        },
        {
            "id": "1002",
            "symbol": "GBPUSD",
            "direction": "sell",
            "volume": 0.02,
            "openPrice": 1.2700,
            "currentPrice": 1.2680,
            "stopLoss": 1.2750,
            "takeProfit": 1.2600,
            "profit": 4.00,
            "openedAt": "2026-06-15T09:00:00Z",
        },
    ]
