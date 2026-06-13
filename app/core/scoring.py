import numpy as np
from datetime import datetime


def score_signal(
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profit: float,
    market: str,
    source: str,
    created_at: datetime = None,
    symbol_win_rate: float = 0.5,
) -> tuple[int, str]:

    score = 0

    # 1. Risk/Reward score (max 30 points)
    if direction == "buy":
        risk = entry_price - stop_loss
        reward = take_profit - entry_price
    else:
        risk = stop_loss - entry_price
        reward = entry_price - take_profit

    if risk > 0:
        rr = reward / risk
        if rr >= 3:
            score += 30
        elif rr >= 2:
            score += 25
        elif rr >= 1.5:
            score += 20
        elif rr >= 1:
            score += 10
        else:
            score += 5

    # 2. Source reliability (max 20 points)
    source_scores = {
        "strategy": 20,
        "tradingview": 15,
        "manual": 10,
        "broker": 18,
    }
    score += source_scores.get(source, 10)

    # 3. Market liquidity (max 20 points)
    market_scores = {
        "forex": 20,
        "crypto": 15,
        "stocks": 18,
        "indices": 17,
        "commodities": 16,
    }
    score += market_scores.get(market, 15)

    # 4. Historical win rate for symbol (max 20 points)
    score += int(symbol_win_rate * 20)

    # 5. Trading session (max 10 points)
    if created_at:
        hour = created_at.hour
        # London/NY overlap 13-17 UTC = best session
        if 13 <= hour <= 17:
            score += 10
        # London open 8-12 UTC
        elif 8 <= hour <= 12:
            score += 7
        # NY open 13-20 UTC
        elif 18 <= hour <= 20:
            score += 5
        else:
            score += 2

    score = max(0, min(100, score))

    if score >= 80:
        grade = "A"
    elif score >= 65:
        grade = "B"
    elif score >= 50:
        grade = "C"
    elif score >= 35:
        grade = "D"
    else:
        grade = "F"

    return score, grade
