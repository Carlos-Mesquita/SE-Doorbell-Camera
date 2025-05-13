from pydantic import BaseModel
from typing import Dict, Set
from fastapi import WebSocket


class ClientInfo(BaseModel):
    websocket: WebSocket
    user_id: str
    rooms: Set[str] = set()
    role: Dict[str, str] = {}

    class Config:
        arbitrary_types_allowed = True


class RoomInfo(BaseModel):
    clients: Set[str] = set()
    broadcasters: Set[str] = set()
    viewers: Set[str] = set()
