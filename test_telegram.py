import asyncio
from app.core.telegram import send_telegram_message

async def test():
    result = await send_telegram_message("Test message from SignalForge API")
    print("Sent:", result)

asyncio.run(test())
