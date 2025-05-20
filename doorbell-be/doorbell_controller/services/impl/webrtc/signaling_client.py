import json
import logging
import asyncio
import websockets  # type: ignore

from typing import Optional, Dict, Any, Awaitable, Callable
from peer_connection_manager import PeerConnectionManager  # Assuming this is correctly defined

logger = logging.getLogger(__name__)


class SignalingClient:
    def __init__(self, peer_manager: PeerConnectionManager, auth_token: str):
        self.peer_manager = peer_manager
        self._auth_token = auth_token

        self._ws: Optional[websockets.WebSocketClientProtocol] = None  # type: ignore
        self.processing_task: Optional[asyncio.Task] = None
        self.is_running = False
        self.current_signaling_url: Optional[str] = None
        self.current_room_id: Optional[str] = None

    async def connect(self, signaling_server_url: str, room_id: str) -> bool:
        if self.is_running:
            if self.current_signaling_url == signaling_server_url and self.current_room_id == room_id:
                logger.info(f"Signaling client already connected and running for {room_id} at {signaling_server_url}.")
                return True
            else:
                logger.warning(
                    f"Signaling client running for different params. Attempting to disconnect and reconnect.")
                await self.disconnect()

        self.current_signaling_url = signaling_server_url
        self.current_room_id = room_id
        full_websocket_url = f"{signaling_server_url}?token={self._auth_token}"

        try:
            logger.info(f"Connecting to signaling server: {full_websocket_url}")
            self._ws = await websockets.connect(full_websocket_url, open_timeout=10)  # type: ignore
            logger.info(f"Successfully connected to signaling server: {full_websocket_url}")
            self.is_running = True

            self.peer_manager.set_on_ice_candidate_callback(self._send_ice_candidate_to_viewer)

            if self.processing_task and not self.processing_task.done():
                self.processing_task.cancel()

            self.processing_task = asyncio.create_task(
                self._process_signaling_messages(room_id),
                name=f"SignalingProcessor_{room_id}"
            )
            return True

        except websockets.exceptions.InvalidURI:
            logger.error(f"Invalid signaling server URI: {full_websocket_url}", exc_info=True)
        except websockets.exceptions.WebSocketException as e:  # Catches connection errors
            logger.error(f"WebSocket connection failed for signaling: {full_websocket_url} - {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to start signaling to {full_websocket_url} for room {room_id}: {e}", exc_info=True)

        self.is_running = False
        self._ws = None
        self.current_signaling_url = None
        self.current_room_id = None
        return False

    async def disconnect(self) -> bool:
        if not self.is_running and not self._ws:
            logger.info("Signaling client already disconnected or not started.")
            return True

        logger.info("Disconnecting signaling client...")
        self.is_running = False

        if self.processing_task and not self.processing_task.done():
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                logger.info("Signaling processing task cancelled successfully.")
            except Exception as e:
                logger.error(f"Error waiting for signaling task during disconnect: {e}", exc_info=True)
        self.processing_task = None

        if self._ws and self._ws.open:
            try:
                await self._ws.close()
                logger.info("Signaling WebSocket connection closed.")
            except Exception as e:
                logger.error(f"Error closing signaling WebSocket: {e}", exc_info=True)
        self._ws = None

        if self.peer_manager:
            await self.peer_manager.cleanup()

        self.current_signaling_url = None
        self.current_room_id = None
        logger.info("Signaling client disconnected.")
        return True

    async def _send_ice_candidate_to_viewer(self, viewer_id: str, rtc_candidate: Any) -> None:
        if not self._ws or not self._ws.open or not self.is_running:
            logger.warning(f"Cannot send ICE candidate to {viewer_id}, WebSocket not connected or not running.")
            return
        if not self.peer_manager.client_id:
            logger.warning(f"Cannot send ICE candidate, broadcaster client_id not set.")
            return

        try:
            logger.debug(f"Sending ICE candidate from {self.peer_manager.client_id} to viewer {viewer_id}")
            message = {
                "type": "ice-candidate",
                "clientId": self.peer_manager.client_id,
                "target": viewer_id,
                "candidate": {
                    "candidate": rtc_candidate.candidate,
                    "sdpMid": rtc_candidate.sdpMid,
                    "sdpMLineIndex": rtc_candidate.sdpMLineIndex,
                }
            }
            await self._ws.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            logger.error(f"Failed to send ICE candidate to {viewer_id}: Signaling connection closed.")
            self.is_running = False  # Mark as not running if connection drops
            # Consider initiating a reconnect or full disconnect
        except Exception as e:
            logger.error(f"Error sending ICE candidate to {viewer_id}: {e}", exc_info=True)

    async def _process_signaling_messages(self, room_id_to_join: str) -> None:
        """Main processing loop for the signaling connection."""

        if not self._ws or not self.is_running:
            logger.error("Signaling message processing cannot start: WebSocket not available or not running.")
            self.is_running = False
            return

        try:
            logger.info("Waiting for registration confirmation from signaling server...")
            try:
                reg_message_str = await asyncio.wait_for(self._ws.recv(), timeout=10.0)
                reg_data = json.loads(reg_message_str)
                if reg_data.get("type") == "registered" and "clientId" in reg_data:
                    self.peer_manager.client_id = reg_data["clientId"]
                    logger.info(f"Registered with signaling server. Client ID: {self.peer_manager.client_id}")
                else:
                    logger.error(f"Unexpected registration message or missing clientId: {reg_data}")
                    await self.disconnect()
                    return
            except asyncio.TimeoutError:
                logger.error("Timeout waiting for registration message from signaling server.")
                await self.disconnect()
                return
            except (json.JSONDecodeError, websockets.exceptions.ConnectionClosed) as e:
                logger.error(f"Error during registration phase: {e}")
                await self.disconnect()
                return

            if not self.peer_manager.client_id:  # Should be set by now
                logger.error("Cannot join room: Broadcaster client_id not set after registration.")
                await self.disconnect()
                return

            join_message = {
                "type": "join",
                "clientId": self.peer_manager.client_id,
                "roomId": room_id_to_join,
                "role": "broadcaster"
            }
            await self._ws.send(json.dumps(join_message))
            logger.info(
                f"Sent join request for room '{room_id_to_join}' as broadcaster '{self.peer_manager.client_id}'.")

            while self.is_running and self._ws and self._ws.open:
                message_str = await self._ws.recv()
                data = json.loads(message_str)
                await self._handle_incoming_message(data)

        except websockets.exceptions.ConnectionClosedOK:
            logger.info("Signaling connection closed gracefully by server or self.")
        except websockets.exceptions.ConnectionClosedError as e:
            logger.warning(f"Signaling connection closed with error: {e}")
        except asyncio.CancelledError:
            logger.info("Signaling message processing task was cancelled.")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from signaling server: {e}. Message: {message_str[:100]}...")
        except Exception as e:
            logger.error(f"Unhandled error in signaling processing loop: {e}", exc_info=True)
        finally:
            logger.info(f"Signaling message processing loop for room {room_id_to_join} stopped.")
            self.is_running = False

    async def _handle_incoming_message(self, data: Dict[str, Any]) -> None:
        msg_type = data.get("type")
        source_client_id = data.get("clientId")

        is_for_this_broadcaster = (
                data.get("target") == self.peer_manager.client_id or
                (data.get("target") == "broadcaster" and msg_type in ["offer", "ice-candidate"])
        )

        if not is_for_this_broadcaster:
            return

        if not source_client_id:
            logger.warning(f"Received message of type '{msg_type}' without a source clientId.")
            return

        if msg_type == "offer":
            sdp = data.get("sdp")
            if not sdp:
                logger.warning(f"Received offer from {source_client_id} without SDP.")
                return

            logger.info(f"Received offer from viewer {source_client_id}. Creating answer...")
            answer_sdp = await self.peer_manager.handle_offer(source_client_id, sdp)
            if answer_sdp:
                await self._ws.send(json.dumps({
                    "type": "answer",
                    "clientId": self.peer_manager.client_id,
                    "target": source_client_id,
                    "sdp": answer_sdp
                }))
                logger.info(f"Sent answer to viewer {source_client_id}.")
            else:
                logger.error(f"Failed to generate answer for offer from {source_client_id}.")


        elif msg_type == "ice-candidate":
            candidate_payload = data.get("candidate")
            if not candidate_payload:
                logger.warning(f"Received ice-candidate message from {source_client_id} without candidate payload.")
                return

            logger.debug(f"Received ICE candidate from viewer {source_client_id}.")
            await self.peer_manager.handle_ice_candidate(source_client_id, candidate_payload)

        elif msg_type == "client-left":
            departed_viewer_id = data.get("clientId")
            if departed_viewer_id:
                logger.info(f"Viewer {departed_viewer_id} left. Cleaning up their PeerConnection.")
                await self.peer_manager.handle_client_left(departed_viewer_id)
            else:
                logger.warning("Received 'client-left' message without a clientId.")

        else:
            logger.debug(f"Received unhandled message type '{msg_type}' from signaling server: {data}")