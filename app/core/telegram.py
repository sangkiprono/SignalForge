import httpx
from app.config import settings

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


async def send_telegram_message(message: str, chat_id: str = None) -> bool:
    chat = chat_id or settings.telegram_chat_id
    if not settings.telegram_bot_token or not chat:
        return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{TELEGRAM_API}/sendMessage",
                json={
                    "chat_id": chat,
                    "text": message,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            return response.status_code == 200
    except Exception:
        return False


async def send_signal_alert(signal) -> bool:
    direction_emoji = "\U0001f7e2" if signal.direction == "buy" else "\U0001f534"
    status_map = {
        "open": "\U0001f514 NEW SIGNAL",
        "tp_hit": "\u2705 TAKE PROFIT HIT",
        "sl_hit": "\u274c STOP LOSS HIT",
        "expired": "\u23f0 SIGNAL EXPIRED",
        "cancelled": "\U0001f6ab SIGNAL CANCELLED",
    }
    header = status_map.get(signal.status, "\U0001f4ca SIGNAL UPDATE")

    message = (
        f"<b>SignalForge API - {header}</b>\n\n"
        f"{direction_emoji} <b>{signal.symbol} {signal.direction.upper()}</b>\n"
        f"\U0001f4ca Market: {signal.market.upper()}\n"
        f"\U0001f4e1 Source: {signal.source.upper()}\n\n"
        f"\U0001f4b0 Entry: <code>{signal.entry_price}</code>\n"
        f"\U0001f6d1 Stop Loss: <code>{signal.stop_loss}</code>\n"
        f"\U0001f3af Take Profit: <code>{signal.take_profit}</code>\n\n"
        f"\U0001f4c8 Risk/Reward: <code>1:{signal.risk_reward_ratio}</code>\n"
        f"\U0001f4c9 Pips Risk: <code>{signal.pips_risk}</code>\n"
        f"\U0001f4c8 Pips Reward: <code>{signal.pips_reward}</code>\n\n"
        f"\U0001f4dd {signal.title}"
    )
    return await send_telegram_message(message)
