from fastapi import APIRouter

router = APIRouter(prefix="/markets", tags=["Markets"])

MARKETS = {
    "forex": [
        "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD",
        "USDCAD", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY"
    ],
    "crypto": [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
        "SOLUSDT", "DOTUSDT", "DOGEUSDT", "MATICUSDT", "LINKUSDT"
    ],
    "stocks": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "NVDA", "META", "NFLX", "AMD", "INTC"
    ],
    "indices": [
        "US30", "US500", "US100", "UK100", "GER40",
        "FRA40", "JP225", "AUS200", "HK50", "ES35"
    ],
    "commodities": [
        "XAUUSD", "XAGUSD", "USOIL", "UKOIL", "NATGAS",
        "WHEAT", "CORN", "COPPER", "PLATINUM", "PALLADIUM"
    ],
}


@router.get("/")
async def get_all_markets():
    return {"markets": list(MARKETS.keys()), "total": len(MARKETS)}


@router.get("/{market}")
async def get_market_symbols(market: str):
    if market not in MARKETS:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Market '{market}' not found")
    return {"market": market, "symbols": MARKETS[market], "count": len(MARKETS[market])}
