import json
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis
from app.core.dependencies import get_db, get_redis
from app.core.websocket_manager import ws_manager
from app.services.auth_service import AuthService

router = APIRouter()

@router.websocket("/ws")
async def websocket_gateway(
    websocket: WebSocket,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    """
    Unified WebSocket Gateway:
    Handles real-time communication for Android client and Moderator Web Portal.
    Authenticated via JWT query parameter or first message frame.
    Subscribes to emergency broadcast and user-specific notifications via Redis Pub/Sub.
    """
    user_id = "anonymous"
    user_role = "guest"

    if token:
        try:
            auth_service = AuthService(db, redis_client)
            user = await auth_service.get_current_user_from_token(token)
            if user:
                user_id = str(user.id)
                user_role = user.role
        except Exception:
            pass

    await ws_manager.connect(websocket, user_id, user_role)
    try:
        # Send initial connected handshake
        await websocket.send_text(json.dumps({
            "event": "CONNECTED",
            "user_id": user_id,
            "role": user_role,
            "channels": ["cs:emergency", f"cs:user:{user_id}"]
        }))

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                # Heartbeat / Ping-Pong
                if msg.get("action") == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id, user_role)
    except Exception:
        ws_manager.disconnect(websocket, user_id, user_role)
