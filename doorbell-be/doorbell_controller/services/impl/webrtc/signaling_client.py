import json
import logging
import asyncio
import websockets  # type: ignore

from typing import Optional, Dict, Any
from aiortc import RTCSessionDescription
from aiortc.sdp import candidate_from_sdp
from .peer_connection_manager import PeerConnectionManager

logger = logging.getLogger(__name__)


class SignalingClient:
    def __init__(self, peer_manager: PeerConnectionManager, auth_token: str):
        self.peer_manager = peer_manager
        self._auth_token = auth_token
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self.processing_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.current_signaling_url: Optional[str] = None
        self.current_room_id: Optional[str] = None
        self.current_viewer_id: Optional[str] = None

    def _is_websocket_open(self) -> bool:
        return self._ws is not None and getattr(self._ws, 'state', 0) == 1

    async def connect(self, signaling_server_url: str, room_id: str) -> bool:
        if self.is_running:
            return True

        self.current_signaling_url = signaling_server_url
        self.current_room_id = room_id
        full_websocket_url = f"{signaling_server_url}?token={self._auth_token}"

        try:
            self._ws = await websockets.connect(full_websocket_url, open_timeout=10)
            self.is_running = True
            self.peer_manager.set_on_ice_candidate_callback(self._send_ice_candidate)
            self.processing_task = asyncio.create_task(self._process_signaling(room_id))
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_running = False
            self._ws = None
            return False

    async def disconnect(self) -> bool:
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        if self._ws and self._is_websocket_open():
            await self._ws.close()
        if self.peer_manager:
            await self.peer_manager.cleanup()
        return True

    async def _send_ice_candidate(self, viewer_id: str, candidate: Any) -> None:
        if not self._ws or not self._is_websocket_open():
            return
        message = {
            "type": "ice-candidate",
            "clientId": self.peer_manager.client_id,
            "target": viewer_id,
            "candidate": {
                "candidate": candidate.candidate,
                "sdpMid": candidate.sdpMid,
                "sdpMLineIndex": candidate.sdpMLineIndex,
            }
        }
        await self._ws.send(json.dumps(message))

    async def _process_signaling(self, room_id: str) -> None:
        try:
            logger.info("Waiting for registration message...")
            reg_message_str = await self._ws.recv()
            logger.info(f"Received registration: {reg_message_str}")

            reg_data = json.loads(reg_message_str)
            if reg_data.get("type") == "registered":
                self.peer_manager.client_id = reg_data.get("clientId")
                logger.info(f"Registered as: {self.peer_manager.client_id}")

                join_msg = {
                    "type": "join",
                    "clientId": self.peer_manager.client_id,
                    "roomId": room_id,
                    "role": "broadcaster"
                }
                logger.info(f"Sending join message: {join_msg}")
                await self._ws.send(json.dumps(join_msg))

                logger.info("Starting message loop...")
                while True:
                    try:
                        message_str = await self._ws.recv()
                        logger.info(f"RECEIVED MESSAGE: {message_str}")

                        data = json.loads(message_str)
                        msg_type = data.get("type")
                        logger.info(f"Message type: {msg_type}, target: {data.get('target')}, from: {data.get('clientId')}")

                        if msg_type == "offer" and (data.get("target") == self.peer_manager.client_id or data.get("target") == "broadcaster"):
                            logger.info("PROCESSING OFFER!")
                            viewer_id = data.get("clientId")
                            self.current_viewer_id = viewer_id

                            if viewer_id in self.peer_manager.peer_connections:
                                await self.peer_manager.peer_connections[viewer_id].close()

                            logger.info(f"Creating peer connection for {viewer_id}")
                            self.peer_manager.peer_connections[viewer_id] = await self.peer_manager.create_peer_connection(viewer_id)
                            pc = self.peer_manager.peer_connections[viewer_id]

                            sdp = data.get("sdp")
                            if not sdp:
                                logger.warning("No SDP in offer!")
                                continue

                            logger.info("Setting remote description and creating answer...")
                            offer = RTCSessionDescription(sdp=sdp, type="offer")
                            await pc.setRemoteDescription(offer)
                            answer = await pc.createAnswer()
                            await pc.setLocalDescription(answer)

                            answer_msg = {
                                "type": "answer",
                                "clientId": self.peer_manager.client_id,
                                "target": viewer_id,
                                "sdp": pc.localDescription.sdp
                            }
                            logger.info(f"Sending answer: {json.dumps(answer_msg)[:200]}...")
                            await self._ws.send(json.dumps(answer_msg))

                        elif msg_type == "ice-candidate" and (data.get("target") == self.peer_manager.client_id or data.get("target") == "broadcaster"):
                            logger.info("PROCESSING ICE CANDIDATE!")
                            viewer_id = data.get("clientId")
                            candidate_data = data.get("candidate")

                            if viewer_id in self.peer_manager.peer_connections and candidate_data:
                                try:
                                    candidate_str = candidate_data.get("candidate", "")
                                    if candidate_str.startswith("candidate:"):
                                        candidate_str = candidate_str[10:]  # EXACT working script logic

                                    ice = candidate_from_sdp(candidate_str)
                                    ice.sdpMid = candidate_data.get("sdpMid", "")
                                    ice.sdpMLineIndex = candidate_data.get("sdpMLineIndex", 0)
                                    await self.peer_manager.peer_connections[viewer_id].addIceCandidate(ice)
                                    logger.info(f"Added ICE candidate from {viewer_id}")
                                except Exception as e:
                                    logger.error(f"Error adding ICE candidate: {e}")

                        elif msg_type == "client-left":
                            logger.info("PROCESSING CLIENT LEFT!")
                            departed_id = data.get("clientId")
                            if departed_id in self.peer_manager.peer_connections:
                                await self.peer_manager.peer_connections[departed_id].close()
                                del self.peer_manager.peer_connections[departed_id]
                                logger.info(f"Closed and removed peer connection for {departed_id}")
                            else:
                                logger.info(f"Client {departed_id} left but no peer connection found (already cleaned up)")
                        else:
                            logger.info(f"Ignoring message type: {msg_type}")

                    except websockets.exceptions.ConnectionClosed:
                        logger.info("WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"Signaling error: {e}", exc_info=True)
            else:
                logger.error(f"Registration failed: {reg_data}")

        except Exception as e:
            logger.error(f"Connection error: {e}", exc_info=True)
        finally:
            logger.info("Signaling process ended")
            self.is_running = False
