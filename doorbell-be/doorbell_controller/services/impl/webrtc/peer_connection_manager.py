import os
from typing import Any, Dict, Optional, Callable, Awaitable, Tuple

from aiortc import RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer
from aiortc.sdp import candidate_from_sdp

from .stream_track import PiCameraTrack  # type: ignore

import time
import hmac
import hashlib
import base64
import logging

logger = logging.getLogger(__name__)


class PeerConnectionManager:
    def __init__(self, picam2, turn_conf: Optional[Dict[str, Any]] = None):
        self.picam2 = picam2
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.client_id: Optional[str] = None
        self.on_ice_candidate_callback: Optional[Callable[[str, Any], Awaitable[None]]] = None

        _turn_conf = turn_conf if turn_conf else {}

        self._turn_host = os.getenv('TURN_HOST')
        self._turn_shared_secret = os.getenv('TURN_SECRET')

        if self._turn_host and not self._turn_shared_secret:
            logger.warning("TURN server host provided but no secret. TURN might not work.")
        if not self._turn_host and self._turn_shared_secret:
            logger.warning("TURN server secret provided but no host. TURN might not work.")

    @staticmethod
    def _create_turn_credential(username_base: str, secret: str) -> Tuple[str, str]:
        expiry = int(time.time()) + 24 * 3600  # 24 hours
        username_with_expiry = f"{expiry}:{username_base}"
        hmac_obj = hmac.new(secret.encode('utf-8'), username_with_expiry.encode('utf-8'), hashlib.sha1)
        credential = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        return username_with_expiry, credential

    def _create_rtc_configuration(self) -> RTCConfiguration:
        ice_servers = []

        if self._turn_host and self._turn_shared_secret:
            turn_username_base = self.client_id if self.client_id else "doorbell_broadcaster"
            username, credential = self._create_turn_credential(turn_username_base, self._turn_shared_secret)

            ice_servers.append(RTCIceServer(
                f"turns:{self._turn_host}:5349?transport=tcp",
                username,
                credential
            ))
            ice_servers.append(RTCIceServer(
                f"turn:{self._turn_host}:3478?transport=udp", 
                username,
                credential
            ))
            logger.info(f"TURN servers configured for {self._turn_host}")
        else:
            logger.info("No TURN configuration - using no ICE servers (local network only)")

        return RTCConfiguration(iceServers=ice_servers)

    def set_on_ice_candidate_callback(self, callback: Callable[[str, Any], Awaitable[None]]):
        self.on_ice_candidate_callback = callback

    async def create_peer_connection(self, viewer_id: str) -> RTCPeerConnection:
        config = self._create_rtc_configuration()
        pc = RTCPeerConnection(configuration=config)

        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate and self.on_ice_candidate_callback:
                await self.on_ice_candidate_callback(viewer_id, candidate)
            elif not candidate:
                logger.info(f"ICE gathering complete for viewer {viewer_id}.")

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state for viewer {viewer_id} is {pc.connectionState}")
            if pc.connectionState == "failed":
                if viewer_id in self.peer_connections:
                    del self.peer_connections[viewer_id]
                    logger.info(f"Removed failed PeerConnection for viewer {viewer_id}")
                await pc.close()
            elif pc.connectionState == "closed":
                logger.info(f"PeerConnection for viewer {viewer_id} closed.")
            elif pc.connectionState == "connected":
                logger.info(f"PeerConnection for viewer {viewer_id} connected successfully!")

        if self.picam2:
            video_track = PiCameraTrack(self.picam2)
            pc.addTrack(video_track)
        else:
            logger.warning("PiCamera2 not available, cannot add video track.")

        self.peer_connections[viewer_id] = pc
        logger.info(f"PeerConnection created for viewer {viewer_id}")
        return pc

    async def handle_offer(self, viewer_id: str, sdp: str) -> Optional[str]:
        logger.info(f"Handling offer from viewer: {viewer_id}")

        if viewer_id in self.peer_connections:
            logger.info(f"Existing PeerConnection found for viewer {viewer_id}, closing it before creating new one.")
            existing_pc = self.peer_connections.pop(viewer_id)
            await existing_pc.close()

        pc = await self.create_peer_connection(viewer_id)

        try:
            offer = RTCSessionDescription(sdp=sdp, type="offer")
            await pc.setRemoteDescription(offer)

            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            return pc.localDescription.sdp if pc.localDescription else None
        except Exception as e:
            logger.error(f"Error handling offer for {viewer_id}: {e}", exc_info=True)
            await pc.close()
            if viewer_id in self.peer_connections:
                del self.peer_connections[viewer_id]
            return None

    async def handle_ice_candidate(self, viewer_id: str, candidate_data: Optional[dict]) -> None:
        if viewer_id not in self.peer_connections:
            logger.warning(f"Received ICE candidate for unknown or closed viewer {viewer_id}")
            return
        if not candidate_data:
            logger.info(f"Received null ICE candidate from viewer {viewer_id}, likely end of candidates.")
            return

        pc = self.peer_connections[viewer_id]
        try:
            candidate_str = candidate_data.get("candidate", "")
            sdp_mid = candidate_data.get("sdpMid")
            sdp_mline_index = candidate_data.get("sdpMLineIndex")

            if not candidate_str:
                logger.info(f"Received ICE candidate data from {viewer_id} with no candidate string.")
                return

            if candidate_str.startswith("candidate:"):
                candidate_str = candidate_str[10:]

            ice_candidate_obj = candidate_from_sdp(candidate_str)
            ice_candidate_obj.sdpMid = sdp_mid
            ice_candidate_obj.sdpMLineIndex = int(sdp_mline_index if sdp_mline_index is not None else 0)

            await pc.addIceCandidate(ice_candidate_obj)
            logger.debug(f"Added ICE candidate from {viewer_id}: {candidate_str[:30]}...")

        except ValueError as ve:
            logger.error(f"Error parsing ICE candidate string for {viewer_id}: {ve} - Data: {candidate_data}")
        except Exception as e:
            logger.error(f"Error adding ICE candidate from {viewer_id}: {e} - Data: {candidate_data}")

    async def handle_client_left(self, client_id_left: str) -> None:
        logger.info(f"Handling client left: {client_id_left}")
        if client_id_left in self.peer_connections:
            pc = self.peer_connections.pop(client_id_left)
            await pc.close()
            logger.info(f"Closed PeerConnection for departed client {client_id_left}.")
        else:
            logger.info(f"Client {client_id_left} left, but no active PeerConnection found.")

    async def cleanup(self) -> None:
        logger.info("Cleaning up all peer connections...")
        for viewer_id in list(self.peer_connections.keys()):
            if viewer_id in self.peer_connections:
                pc = self.peer_connections.pop(viewer_id)
                try:
                    for sender in pc.getSenders():
                        if sender.track and isinstance(sender.track, PiCameraTrack):
                            sender.track.stop()
                    await pc.close()
                except Exception as e:
                    logger.error(f"Error closing peer connection for {viewer_id} during cleanup: {e}")
        self.peer_connections.clear()
        logger.info("All peer connections cleaned up.")

    def get_connections_count(self) -> int:
        return len(self.peer_connections)
