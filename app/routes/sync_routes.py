import json
from collections import defaultdict
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.core.security import decode_access_token

router = APIRouter(tags=["Sync"])


class SyncConnectionManager:
    def __init__(self) -> None:
        self.rooms: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, room_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.rooms[room_id].append(websocket)

    def disconnect(self, room_id: str, websocket: WebSocket) -> None:
        room = self.rooms.get(room_id)
        if room is None:
            return
        if websocket in room:
            room.remove(websocket)
        if not room:
            self.rooms.pop(room_id, None)

    async def broadcast(self, room_id: str, message: dict) -> None:
        dead_connections: list[WebSocket] = []
        for connection in self.rooms.get(room_id, []):
            try:
                await connection.send_json(message)
            except RuntimeError:
                dead_connections.append(connection)
        for connection in dead_connections:
            self.disconnect(room_id, connection)


async def broadcast_sync_event(room_id: str, event_type: str, payload: dict[str, Any] | None = None) -> None:
    await manager.broadcast(
        room_id,
        {
            "type": event_type,
            "roomId": room_id,
            "payload": payload or {},
        },
    )


manager = SyncConnectionManager()


@router.websocket("/ws/sync/{room_id}")
async def sync_room(websocket: WebSocket, room_id: str) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token required")
        return
    try:
        payload = decode_access_token(token)
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    await manager.connect(room_id, websocket)
    await manager.broadcast(
        room_id,
        {
            "type": "presence",
            "action": "join",
            "roomId": room_id,
            "userId": payload.get("sub"),
            "role": payload.get("role"),
        },
    )
    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                parsed_message = json.loads(raw_message)
            except json.JSONDecodeError:
                continue
            await manager.broadcast(
                room_id,
                {
                    "type": parsed_message.get("type", "sync"),
                    "roomId": room_id,
                    "userId": payload.get("sub"),
                    "role": payload.get("role"),
                    "payload": parsed_message.get("payload"),
                },
            )
    except WebSocketDisconnect:
        manager.disconnect(room_id, websocket)
        await manager.broadcast(
            room_id,
            {
                "type": "presence",
                "action": "leave",
                "roomId": room_id,
                "userId": payload.get("sub"),
                "role": payload.get("role"),
            },
        )
