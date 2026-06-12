from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websocket_manager import manager
from app.core.security import decode_access_token

router = APIRouter(prefix="/ws", tags=["WebSocket"])


@router.websocket("/signals")
async def websocket_signals(
    websocket: WebSocket,
    token: str = Query(None),
):
    user_id = None
    if token:
        payload = decode_access_token(token)
        if payload:
            user_id = payload.get("sub")

    await manager.connect(websocket, user_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to SignalForge real-time feed",
            "user_id": user_id,
        })
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "message": "alive"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
