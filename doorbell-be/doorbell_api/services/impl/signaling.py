from typing import Dict, Set, List, Optional
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

    async def register_client(self, connection_id: str, websocket: WebSocket, user_id_from_token: str) -> None:
        if connection_id in self._clients:
            self._logger.warning(f"Attempted to register already existing connection_id: {connection_id}")
            await self._clients[connection_id].websocket.close(reason="Re-registration attempt")

        self._clients[connection_id] = ClientInfo(websocket=websocket, user_id=user_id_from_token)
        self._logger.info(f"Signaling client registered. Connection ID: {connection_id}, User ID: {user_id_from_token}")

    async def unregister_client(self, connection_id: str) -> None:
        if connection_id in self._clients:
            client_info = self._clients[connection_id]
            self._logger.info(
                f"Unregistering signaling client. Connection ID: {connection_id}, User ID: {client_info.user_id}")

            rooms_to_leave = list(client_info.rooms)
            for room_id in rooms_to_leave:
                await self.leave_room(connection_id, room_id)

            del self._clients[connection_id]
            self._logger.info(f"Signaling client {connection_id} unregistered.")
        else:
            self._logger.warning(f"Attempt to unregister non-existent client connection_id: {connection_id}")

    async def handle_message(self, sender_connection_id: str, message: dict) -> Optional[dict]:
        if sender_connection_id not in self._clients:
            self._logger.warning(f"Message from unregistered connection_id: {sender_connection_id}")
            return {"type": "error", "message": "Client (connection) not registered"}

        message_type = message.get("type")

        if not message_type:
            return {"type": "error", "message": "Invalid message: missing type"}

        if message_type in ["offer", "answer", "ice-candidate"]:
            target_specifier = message.get("target")
            room_id_context = message.get("roomId")

            actual_target_connection_id: Optional[str] = None

            if target_specifier == "broadcaster" and room_id_context:
                if room_id_context in self._rooms:
                    room = self._rooms[room_id_context]
                    if len(room.broadcasters) == 1:
                        actual_target_connection_id = next(
                            iter(room.broadcasters))
                    elif len(room.broadcasters) == 0:
                        self._logger.warning(
                            f"Message for broadcaster in room {room_id_context}, but no broadcaster found.")
                        return {"type": "error", "message": f"No broadcaster in room {room_id_context}"}
                    else:
                        self._logger.warning(
                            f"Multiple broadcasters in room {room_id_context}. Target 'broadcaster' is ambiguous.")
                        return {"type": "error",
                                "message": f"Room {room_id_context} has multiple broadcasters, target 'broadcaster' is ambiguous."}
                else:
                    self._logger.warning(f"Room {room_id_context} not found for 'broadcaster' target.")
                    return {"type": "error", "message": f"Room {room_id_context} not found"}
            elif target_specifier and target_specifier != "broadcaster":
                actual_target_connection_id = target_specifier

            if actual_target_connection_id and actual_target_connection_id in self._clients:
                try:
                    payload_to_forward = message.copy()
                    payload_to_forward["clientId"] = sender_connection_id
                    await self._clients[actual_target_connection_id].websocket.send_text(json.dumps(payload_to_forward))
                    self._logger.info(
                        f"Forwarded '{message_type}' from conn {sender_connection_id} to conn {actual_target_connection_id}")
                    return None
                except Exception as e:
                    self._logger.error(
                        f"Error forwarding message from {sender_connection_id} to {actual_target_connection_id}: {e}",
                        exc_info=True)
                    return {"type": "error", "message": f"Error forwarding message: {str(e)}"}
            else:
                self._logger.warning(
                    f"Target client/connection '{actual_target_connection_id or target_specifier}' not found for message type '{message_type}'.")
                return {"type": "error",
                        "message": f"Target client '{actual_target_connection_id or target_specifier}' not found"}

        elif message_type == "join":
            room_id = message.get("roomId")
            role = message.get("role", "viewer")  # "broadcaster" for RPi, "viewer" for phone
            if not room_id: return {"type": "error", "message": "Missing roomId in join request"}
            return await self.join_room(sender_connection_id, room_id, role)

        elif message_type == "leave":
            room_id = message.get("roomId")
            if not room_id: return {"type": "error", "message": "Missing roomId in leave request"}
            return await self.leave_room(sender_connection_id, room_id)

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
            self._logger.warning(f"Unknown message type '{message_type}' from conn {sender_connection_id}")
            return {"type": "error", "message": f"Unknown message type: {message_type}"}

    async def join_room(self, connection_id: str, room_id: str, role: str = "viewer") -> dict:
        if connection_id not in self._clients:
            return {"type": "error", "message": "Client (connection) not registered"}

        if room_id not in self._rooms:
            self._rooms[room_id] = RoomInfo()

        room = self._rooms[room_id]
        client_info = self._clients[connection_id]

        if connection_id in room.clients:
            self._logger.warning(
                f"Connection {connection_id} already in room {room_id}. Role: {client_info.role.get(room_id)}")

        room.clients.add(connection_id)
        client_info.rooms.add(room_id)
        client_info.role[room_id] = role

        if role == "broadcaster":
            if len(room.broadcasters) > 0 and connection_id not in room.broadcasters:
                other_broadcaster = next(iter(room.broadcasters))
                self._logger.warning(
                    f"Room {room_id} already has a broadcaster ({other_broadcaster}). Conn {connection_id} cannot join as broadcaster.")
                room.clients.remove(connection_id)
                client_info.rooms.remove(room_id)
                del client_info.role[room_id]
                return {"type": "error", "message": f"Room {room_id} already has a broadcaster."}
            room.broadcasters.add(connection_id)
            room.viewers.discard(connection_id)
        else:
            room.viewers.add(connection_id)
            room.broadcasters.discard(connection_id)

        self._logger.info(f"Connection {connection_id} (User: {client_info.user_id}) joined room {room_id} as {role}")

        await self._notify_room_clients(room_id, {
            "type": "client-joined", "roomId": room_id, "clientId": connection_id, "role": role
        }, exclude_self_id=connection_id)

        return {"type": "joined", "roomId": room_id, "role": role, "clients": self.get_room_clients(room_id)}

    async def leave_room(self, connection_id: str, room_id: str) -> dict:
        if connection_id not in self._clients:
            return {"type": "error", "message": f"Client (connection) {connection_id} not found for leaving room."}
        if room_id not in self._rooms:
            return {"type": "error", "message": f"Room {room_id} not found for leaving."}

        room = self._rooms[room_id]
        client_info = self._clients[connection_id]

        if connection_id not in room.clients:
            return {"type": "error", "message": f"Connection {connection_id} not in room {room_id}"}

        room.clients.remove(connection_id)
        if connection_id in client_info.rooms: client_info.rooms.remove(room_id)

        role_left = client_info.role.pop(room_id, None)

        if role_left == "broadcaster": room.broadcasters.discard(connection_id)
        if role_left == "viewer": room.viewers.discard(connection_id)

        self._logger.info(
            f"Connection {connection_id} (User: {client_info.user_id}, Role: {role_left}) left room {room_id}")

        if not room.clients:
            del self._rooms[room_id]
            self._logger.info(f"Room {room_id} deleted (no clients).")
        else:
            await self._notify_room_clients(room_id, {
                "type": "client-left", "roomId": room_id, "clientId": connection_id
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
        if room_id not in self._rooms: return []
        room = self._rooms[room_id]
        client_list = []
        for conn_id in room.clients:
            if conn_id in self._clients:
                client_info = self._clients[conn_id]
                client_list.append({
                    "clientId": conn_id,
                    "userId": client_info.user_id,
                    "role": client_info.role.get(room_id, "unknown")
                })
        return client_list

    async def _notify_room_clients(self, room_id: str, message: dict, exclude_self_id: Optional[str] = None) -> None:
        if room_id not in self._rooms: return
        room = self._rooms[room_id]
        message_json = json.dumps(message)

        for conn_id in list(room.clients):
            if conn_id == exclude_self_id: continue
            if conn_id in self._clients:
                try:
                    await self._clients[conn_id].websocket.send_text(message_json)
                except Exception as e:
                    self._logger.error(f"Error notifying client {conn_id} in room {room_id}: {e}. Removing.")
                    await self.unregister_client(conn_id)
            else:
                 self._logger.warning(f"Client {conn_id} in room {room_id} but not in master client list. Removing from room.")
                 room.clients.discard(conn_id)
                 room.broadcasters.discard(conn_id)
                 room.viewers.discard(conn_id)

    async def broadcast_to_room(self, room_id: str, message: dict) -> None:
        await self._notify_room_clients(room_id, message)
