import json
import logging
import asyncio
import websockets

from typing import Optional, Dict, Any
from peer_connection_manager import PeerConnectionManager

logger = logging.getLogger(__name__)


class SignalingClient:
    """WebSocket client for WebRTC signaling."""

    def __init__(self, peer_manager: PeerConnectionManager, token, ws_client):
        self.peer_manager = peer_manager
        self._ws_client = ws_client
        self._auth_token = token
        self.task: Optional[asyncio.Task] = None
        self.is_running = False

    async def connect(self, room_id: str) -> bool:
        """Connect to the signaling server and join a room."""
        if self.is_running:
            logger.info("Signaling client already running")
            return True

        try:
            self.is_running = True

            # Set up the ice candidate callback
            self.peer_manager.set_on_ice_candidate(self._send_ice_candidate)

            self.task = asyncio.create_task(
                self._process_signaling(room_id)
            )

            await asyncio.sleep(1)
            return True

        except Exception as e:
            logger.error(f"Failed to start signaling: {e}")
            self.is_running = False
            return False

    async def disconnect(self) -> bool:
        """Disconnect from the signaling server."""
        if not self.is_running:
            return True

        try:
            self.is_running = False
            if self.task and not self.task.done():
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass

            await self.peer_manager.cleanup()
            return True

        except Exception as e:
            logger.error(f"Error disconnecting signaling: {e}")
            return False

    async def _send_ice_candidate(self, viewer_id: str, candidate) -> None:
        """Send an ICE candidate to a viewer."""
        if not self._ws_client:
            return

        try:
            await self._ws_client.send(json.dumps({
                "type": "ice-candidate",
                "clientId": self.peer_manager.client_id,
                "target": viewer_id,
                "candidate": {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                }
            }))
        except Exception as e:
            logger.error(f"Error sending ICE candidate: {e}")

    async def _process_signaling(self, room_id: str) -> None:
        """Main processing loop for the signaling connection."""
        reconnect_delay = 5  # seconds

        while self.is_running:
            try:
                # Handle registration
                reg_data = json.loads(await self._ws_client.recv())
                if reg_data.get("type") != "registered":
                    logger.error(f"Registration failed: {reg_data}")
                    await asyncio.sleep(reconnect_delay)
                    continue

                # Store client ID and join room
                self.peer_manager.client_id = reg_data.get("clientId")
                logger.info(f"Registered as: {self.peer_manager.client_id}")

                await self._ws_client.send(json.dumps({
                    "type": "join",
                    "clientId": self.peer_manager.client_id,
                    "roomId": room_id,
                    "role": "broadcaster"
                }))

                # Process messages
                while self.is_running:
                    try:
                        data = json.loads(await self._ws_client.recv())
                        await self._handle_message(data)
                    except websockets.exceptions.ConnectionClosed:
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

            except Exception as e:
                logger.error(f"Signaling connection error: {e}")

            if self.is_running:
                logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                await asyncio.sleep(reconnect_delay)

    async def _handle_message(self, data: Dict[str, Any]) -> None:
        """Handle a message from the signaling server."""
        msg_type = data.get("type")

        if msg_type == "offer" and (data.get("target") == self.peer_manager.client_id or data.get("target") == "broadcaster"):
            viewer_id = data.get("clientId")
            sdp = data.get("sdp")

            if not sdp:
                return

            # Process the offer and send an answer
            answer_sdp = await self.peer_manager.handle_offer(viewer_id, sdp)

            await self._ws_client.send(json.dumps({
                "type": "answer",
                "clientId": self.peer_manager.client_id,
                "target": viewer_id,
                "sdp": answer_sdp
            }))

        elif msg_type == "ice-candidate" and (data.get("target") == self.peer_manager.client_id or
                                              data.get("target") == "broadcaster"):
            viewer_id = data.get("clientId")
            candidate_data = data.get("candidate")

            await self.peer_manager.handle_ice_candidate(viewer_id, candidate_data)

        elif msg_type == "client-left":
            departed_id = data.get("clientId")
            await self.peer_manager.handle_client_left(departed_id)
