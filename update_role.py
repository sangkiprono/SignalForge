import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.config import settings

async def update():
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE users SET role = 'trader' WHERE email = 'test@example.com'"))
    print('Done')

asyncio.run(update())
