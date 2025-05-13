from typing import Dict, Set, List
from fastapi import WebSocket
import logging
import json

from doorbell_api.dtos import ClientInfo, RoomInfo
from doorbell_api.services import IWebRTCSignalingService


class WebRTCSignalingService(IWebRTCSignalingService):
    def __init__(self):
        self._clients: Dict[str, ClientInfo] = {}
        self._rooms: Dict[str, RoomInfo] = {}
        self._logger = logging.getLogger(__name__)

    async def register_client(self, user_id: str, websocket: WebSocket) -> None:
        self._clients[user_id] = ClientInfo(websocket=websocket)
        self._logger.info(f"Client {user_id} registered")

    async def unregister_client(self, client_id: str) -> None:
        if client_id in self._clients:
            client = self._clients[client_id]

            rooms_to_leave = client.rooms.copy()
            for room_id in rooms_to_leave:
                await self.leave_room(client_id, room_id)

            del self._clients[client_id]
            self._logger.info(f"Client {client_id} unregistered")

    async def handle_message(self, client_id: str, message: dict) -> dict:
        if client_id not in self._clients:
            return {"type": "error", "message": "Client not registered"}

        message_type = message.get("type")

        if not message_type:
            return {"type": "error", "message": "Invalid message: missing type"}

        if message_type in ["offer", "answer", "ice-candidate"]:
            target_id = message.get("target")
            room_id = message.get("roomId")

            if target_id == "broadcaster" and room_id:
                if room_id in self._rooms:
                    room = self._rooms[room_id]
                    if len(room.broadcasters) == 1:
                        target_id = next(iter(room.broadcasters))
                    else:
                        return {
                            "type": "error",
                            "message": f"Room {room_id} has {len(room.broadcasters)} broadcasters, specify which one"
                        }
                else:
                    return {"type": "error", "message": f"Room {room_id} not found"}

            if target_id and target_id in self._clients:
                try:
                    if "senderId" not in message:
                        message["senderId"] = client_id

                    await self._clients[target_id].websocket.send_text(json.dumps(message))

                    self._logger.info(
                        f"Forwarded {message_type} from {client_id} to {target_id}"
                    )

                    return {"type": "success", "message": "Message forwarded"}
                except Exception as e:
                    self._logger.error(f"Error forwarding message: {str(e)}")
                    return {"type": "error", "message": f"Error forwarding message: {str(e)}"}
            else:
                return {"type": "error", "message": f"Target client {target_id} not found"}

        elif message_type == "join":
            room_id = message.get("roomId")
            role = message.get("role", "viewer")

            if not room_id:
                return {"type": "error", "message": "Missing roomId in join request"}

            return await self.join_room(client_id, room_id, role)

        elif message_type == "leave":
            room_id = message.get("roomId")

            if not room_id:
                return {"type": "error", "message": "Missing roomId in leave request"}

            return await self.leave_room(client_id, room_id)

        elif message_type == "get-room-info":
            room_id = message.get("roomId")

            if not room_id:
                return {"type": "error", "message": "Missing roomId in get-room-info request"}

            clients = self.get_room_clients(room_id)
            return {
                "type": "room-info",
                "roomId": room_id,
                "clients": clients
            }

        else:
            return {"type": "error", "message": f"Unknown message type: {message_type}"}

    async def join_room(self, client_id: str, room_id: str, role: str = "viewer") -> dict:
        if client_id not in self._clients:
            return {"type": "error", "message": "Client not registered"}

        if room_id not in self._rooms:
            self._rooms[room_id] = RoomInfo()

        room = self._rooms[room_id]
        client = self._clients[client_id]

        room.clients.add(client_id)
        client.rooms.add(room_id)


        client.role[room_id] = role

        if role == "broadcaster":
            room.broadcasters.add(client_id)
        else:
            room.viewers.add(client_id)

        self._logger.info(f"Client {client_id} joined room {room_id} as {role}")

        await self._notify_room_clients(room_id, {
            "type": "client-joined",
            "roomId": room_id,
            "clientId": client_id,
            "role": role
        })

        return {
            "type": "joined",
            "roomId": room_id,
            "role": role,
            "clients": self.get_room_clients(room_id)
        }

    async def leave_room(self, client_id: str, room_id: str) -> dict:
        if client_id not in self._clients or room_id not in self._rooms:
            return {"type": "error", "message": "Client or room not found"}

        room = self._rooms[room_id]
        client = self._clients[client_id]

        if client_id not in room.clients:
            return {"type": "error", "message": f"Client {client_id} not in room {room_id}"}

        room.clients.remove(client_id)
        client.rooms.remove(room_id)

        if client_id in room.broadcasters:
            room.broadcasters.remove(client_id)
        if client_id in room.viewers:
            room.viewers.remove(client_id)

        if room_id in client.role:
            del client.role[room_id]

        self._logger.info(f"Client {client_id} left room {room_id}")

        if not room.clients:
            del self._rooms[room_id]
            self._logger.info(f"Room {room_id} deleted (no clients)")
        else:
            await self._notify_room_clients(room_id, {
                "type": "client-left",
                "roomId": room_id,
                "clientId": client_id
            })

        return {"type": "left", "roomId": room_id}

    def get_active_rooms(self) -> List[dict]:
        rooms = []
        for room_id, room in self._rooms.items():
            rooms.append({
                "roomId": room_id,
                "totalClients": len(room.clients),
                "broadcasters": len(room.broadcasters),
                "viewers": len(room.viewers)
            })
        return rooms

    def get_room_clients(self, room_id: str) -> List[dict]:
        if room_id not in self._rooms:
            return []

        room = self._rooms[room_id]
        clients = []

        for client_id in room.clients:
            if client_id in self._clients:
                client = self._clients[client_id]
                clients.append({
                    "clientId": client_id,
                    "userId": client.user_id,
                    "role": client.role.get(room_id, "unknown")
                })

        return clients

    async def _notify_room_clients(self, room_id: str, message: dict) -> None:
        if room_id not in self._rooms:
            return

        room = self._rooms[room_id]
        message_json = json.dumps(message)

        for client_id in room.clients:
            if client_id in self._clients:
                try:
                    await self._clients[client_id].websocket.send_text(message_json)
                except Exception as e:
                    self._logger.error(f"Error notifying client {client_id}: {str(e)}")

    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        await self._notify_room_clients(room_id, message)
