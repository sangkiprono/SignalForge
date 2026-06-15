import asyncio
from metaapi_cloud_sdk import MetaApi
from app.config import settings


async def get_account_info():
    api = MetaApi(settings.metaapi_token)
    try:
        account = await api.metatrader_account_api.get_account(settings.metaapi_account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        info = await connection.get_account_information()
        await connection.close()
        return info
    except Exception as e:
        return {"error": str(e)}


async def place_trade(
    symbol: str,
    direction: str,
    volume: float,
    stop_loss: float,
    take_profit: float,
    comment: str = "SignalForge",
):
    api = MetaApi(settings.metaapi_token)
    try:
        account = await api.metatrader_account_api.get_account(settings.metaapi_account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()

        if direction == "buy":
            result = await connection.create_market_buy_order(
                symbol, volume, stop_loss, take_profit, {"comment": comment}
            )
        else:
            result = await connection.create_market_sell_order(
                symbol, volume, stop_loss, take_profit, {"comment": comment}
            )

        await connection.close()
        return result
    except Exception as e:
        return {"error": str(e)}


async def get_open_positions():
    api = MetaApi(settings.metaapi_token)
    try:
        account = await api.metatrader_account_api.get_account(settings.metaapi_account_id)
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        positions = await connection.get_positions()
        await connection.close()
        return positions
    except Exception as e:
        return {"error": str(e)}
