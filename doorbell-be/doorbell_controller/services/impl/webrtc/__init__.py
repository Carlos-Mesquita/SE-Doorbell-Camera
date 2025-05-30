import logging
from typing import Dict, Any, Optional

from .peer_connection_manager import PeerConnectionManager
from .signaling_client import SignalingClient

logger = logging.getLogger(__name__)


class WebRTCManager:
    def __init__(self, picam2, turn_config: Optional[Dict[str, Any]] = None):
        self.picam2 = picam2
        self.peer_manager: Optional[PeerConnectionManager] = None
        self.signaling_client: Optional[SignalingClient] = None
        self.turn_config = turn_config if turn_config else {}

    async def start_streaming(self, signaling_server_url: str, room_id: str, auth_token: str) -> bool:
        try:
            logger.info(f"Attempting to start WebRTC streaming in room {room_id} via {signaling_server_url}")

            if self.signaling_client and self.signaling_client.is_running:
                logger.info("WebRTC streaming already active or being started.")
                return True

            if not self.peer_manager:
                self.peer_manager = PeerConnectionManager(self.picam2, self.turn_config)

            if not self.signaling_client:
                self.signaling_client = SignalingClient(self.peer_manager, auth_token)

            success = await self.signaling_client.connect(signaling_server_url, room_id)
            if success:
                logger.info(f"WebRTC signaling client connected for room {room_id}.")
            else:
                logger.error(f"Failed to connect WebRTC signaling client for room {room_id}.")
                if self.signaling_client: await self.signaling_client.disconnect()
                self.signaling_client = None
            return success

        except Exception as e:
            logger.error(f"Error starting WebRTC stream: {e}", exc_info=True)
            if self.signaling_client:
                await self.signaling_client.disconnect()
                self.signaling_client = None
            return False

    async def stop_streaming(self) -> bool:
        stopped_successfully = True
        try:
            logger.info("Stopping WebRTC streaming")

            if self.signaling_client:
                logger.info("Disconnecting signaling client...")
                success = await self.signaling_client.disconnect()
                if not success:
                    logger.warning("Signaling client did not disconnect cleanly.")
                    stopped_successfully = False
                self.signaling_client = None
            else:
                logger.info("No active signaling client to stop.")


            if self.peer_manager:
                logger.info("Cleaning up peer manager...")
                await self.peer_manager.cleanup()
                self.peer_manager = None
            else:
                logger.info("No active peer manager to clean up.")

            logger.info(f"WebRTC streaming stop attempt finished. Success: {stopped_successfully}")
            return stopped_successfully

        except Exception as e:
            logger.error(f"Error stopping WebRTC stream: {e}", exc_info=True)
            return False

    async def get_streaming_status(self) -> Dict[str, Any]:
        active = self.signaling_client is not None and self.signaling_client.is_running
        connections_count = 0
        client_id = None

        if active and self.peer_manager:
            connections_count = self.peer_manager.get_connections_count()
            client_id = self.peer_manager.client_id

        status = {
            "active": active,
            "connections": connections_count,
            "client_id": client_id,
            "room_id": self.signaling_client.current_room_id if self.signaling_client else None,
        }
        return status

__all__ = [
    "WebRTCManager"
]