import logging
import os
from typing import Dict, Any, Optional

from peer_connection_manager import PeerConnectionManager
from signaling_client import SignalingClient

logger = logging.getLogger(__name__)


class WebRTCManager:

    def __init__(self, picam2, ws):
        self.picam2 = picam2
        self.peer_manager = None
        self.signaling_client = None
        self.ws = ws
        self.turn_secret = os.getenv("TURN_SERVER_SECRET")

    async def start_streaming(self, signaling_server: str, room_id: str, auth_token: str) -> bool:
        try:
            logger.info(f"Starting WebRTC streaming in room {room_id}")

            if not self.peer_manager:
                self.peer_manager = PeerConnectionManager(self.picam2, self.turn_secret)

            if not self.signaling_client:
                self.signaling_client = SignalingClient(self.peer_manager, self.ws)

            success = await self.signaling_client.connect(signaling_server, room_id, auth_token)
            return success

        except Exception as e:
            logger.error(f"Error starting WebRTC stream: {e}")
            return False

    async def stop_streaming(self) -> bool:
        try:
            logger.info("Stopping WebRTC streaming")

            if self.signaling_client:
                success = await self.signaling_client.disconnect()
                if not success:
                    return False

            self.signaling_client = None
            self.peer_manager = None

            return True

        except Exception as e:
            logger.error(f"Error stopping WebRTC stream: {e}")
            return False

    async def get_streaming_status(self) -> Dict[str, Any]:
        active = self.signaling_client is not None and self.peer_manager is not None

        status = {
            "active": active,
            "connections": 0,
        }

        if active and self.peer_manager:
            status["connections"] = self.peer_manager.get_connections_count()

        return status
