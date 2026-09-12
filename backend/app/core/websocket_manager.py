import asyncio
import json
import uuid
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

class WebSocketManager:
    """
    Centralized WebSocket Gateway backed by Redis Pub/Sub.
    Handles multiplexed real-time messaging across mobile clients and moderator portals.
    """

    def __init__(self):
        # user_id -> set of active WebSockets
        self.user_connections: Dict[str, Set[WebSocket]] = {}
        # role -> set of active WebSockets
        self.role_connections: Dict[str, Set[WebSocket]] = {}
        # broadcast listeners
        self.broadcast_connections: Set[WebSocket] = set()
        self._listener_task: Optional[asyncio.Task] = None

    async def connect(self, websocket: WebSocket, user_id: str, role: str):
        await websocket.accept()
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)

        if role not in self.role_connections:
            self.role_connections[role] = set()
        self.role_connections[role].add(websocket)

        self.broadcast_connections.add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str, role: str):
        if user_id in self.user_connections:
            self.user_connections[user_id].discard(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        if role in self.role_connections:
            self.role_connections[role].discard(websocket)
            if not self.role_connections[role]:
                del self.role_connections[role]

        self.broadcast_connections.discard(websocket)

    async def send_personal_message(self, message: dict, user_id: str):
        sockets = self.user_connections.get(user_id, set()).copy()
        payload = json.dumps(message)
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                pass

    async def broadcast_to_role(self, message: dict, role: str):
        sockets = self.role_connections.get(role, set()).copy()
        payload = json.dumps(message)
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                pass

    async def broadcast(self, message: dict):
        sockets = self.broadcast_connections.copy()
        payload = json.dumps(message)
        for ws in sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                pass

    async def publish_event(self, redis_client: redis.Redis, channel: str, event_data: dict):
        """
        Publishes event to Redis Pub/Sub so all backend workers receive and fan out to their WS clients.
        """
        if redis_client:
            try:
                await redis_client.publish(channel, json.dumps(event_data))
            except Exception:
                pass
        # Also fan out locally in case Redis pubsub isn't running in a multi-node cluster
        if channel == "cs:emergency":
            await self.broadcast(event_data)
        elif channel.startswith("cs:role:"):
            target_role = channel.replace("cs:role:", "")
            await self.broadcast_to_role(event_data, target_role)
        elif channel.startswith("cs:user:"):
            target_uid = channel.replace("cs:user:", "")
            await self.send_personal_message(event_data, target_uid)

    async def start_redis_listener(self, redis_client: redis.Redis):
        """
        Subscribes to Redis Pub/Sub and dispatches incoming messages to connected WebSockets.
        """
        if redis_client is None:
            return

        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("cs:emergency", "cs:broadcast")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message.get("data"):
                    try:
                        raw_data = message["data"]
                        if isinstance(raw_data, bytes):
                            raw_data = raw_data.decode("utf-8")
                        payload = json.loads(raw_data)
                        chan = message.get("channel")
                        if isinstance(chan, bytes):
                            chan = chan.decode("utf-8")

                        if chan == "cs:emergency":
                            await self.broadcast(payload)
                        elif chan == "cs:broadcast":
                            await self.broadcast(payload)
                    except Exception:
                        pass
                await asyncio.sleep(0.05)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

# Global Singleton Manager
ws_manager = WebSocketManager()
