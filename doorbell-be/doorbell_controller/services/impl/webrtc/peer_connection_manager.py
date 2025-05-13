import os
from typing import Any, Dict, Optional, Callable

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp

from pi_camera_track import PiCameraTrack

import time
import hmac
import hashlib
import base64
import logging

from aiortc import RTCConfiguration, RTCIceServer

logger = logging.getLogger(__name__)


class PeerConnectionManager:
    """ Manages WebRTC peer connections for multiple viewers. """

    def __init__(self, picam2, turn_conf: Dict[str, Any]):
        self.picam2 = picam2
        self.peer_connections: Dict[str, RTCPeerConnection] = {}
        self.client_id: Optional[str] = None
        self.current_viewer_id: Optional[str] = None
        self.on_ice_candidate: Optional[Callable] = None
        self._turn_host = turn_conf['host']
        self._turn_secret = turn_conf['secret']

    @staticmethod
    def create_credential(username_base, secret):
        """Create time-limited TURN credentials using HMAC-SHA1."""
        expiry = int(time.time()) + 24 * 3600
        username_with_expiry = f"{expiry}:{username_base}"
        hmac_obj = hmac.new(secret.encode(), username_with_expiry.encode(), hashlib.sha1)
        credential = base64.b64encode(hmac_obj.digest()).decode()
        return username_with_expiry, credential

    def create_rtc_configuration(self, client_id, turn_secret):
        """Create RTCConfiguration with STUN and TURN servers."""
        username_with_expiry, credential = self.create_credential(
            client_id or "broadcaster",
            turn_secret
        )

        config = RTCConfiguration(
            iceServers=[
                RTCIceServer(
                    f"turns:{self._turn_host}:5349?transport=tcp",
                    username_with_expiry,
                    credential
                ),
                RTCIceServer(
                    f"turn:{self._turn_secret}:3478?transport=udp",
                    username_with_expiry,
                    credential
                )
            ]
        )

        return config

    def set_on_ice_candidate(self, callback):
        """Set callback for ICE candidates."""
        self.on_ice_candidate = callback

    def create_peer_connection(self, viewer_id: str) -> RTCPeerConnection:
        """Create a new peer connection for a viewer."""
        config = WebRTCCredentials.create_rtc_configuration(self.client_id, self.turn_secret)
        pc = RTCPeerConnection(configuration=config)

        # Set up ICE candidate handler
        @pc.on("icecandidate")
        async def on_icecandidate(candidate):
            if candidate and self.on_ice_candidate:
                await self.on_ice_candidate(viewer_id, candidate)

        # Handle connection state changes
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state for {viewer_id} is {pc.connectionState}")
            if pc.connectionState == "failed" and viewer_id in self.peer_connections:
                del self.peer_connections[viewer_id]
                await pc.close()

        # Create and add video track
        video = PiCameraTrack(self.picam2)
        pc.addTrack(video)

        # Store the connection
        self.peer_connections[viewer_id] = pc
        return pc

    async def handle_offer(self, viewer_id: str, sdp: str) -> str:
        """Process an offer and create an answer."""
        self.current_viewer_id = viewer_id

        # Close existing connection if any
        if viewer_id in self.peer_connections:
            await self.peer_connections[viewer_id].close()

        # Create a new connection
        pc = self.create_peer_connection(viewer_id)

        # Set remote description (the offer)
        offer = RTCSessionDescription(sdp=sdp, type="offer")
        await pc.setRemoteDescription(offer)

        # Create and set local description (the answer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return pc.localDescription.sdp

    async def handle_ice_candidate(self, viewer_id: str, candidate_data: dict) -> None:
        """Process an ICE candidate from a viewer."""
        if viewer_id not in self.peer_connections or not candidate_data:
            return

        try:
            candidate_str = candidate_data.get("candidate", "")
            if candidate_str.startswith("candidate:"):
                candidate_str = candidate_str[10:]

            ice = candidate_from_sdp(candidate_str)
            ice.sdpMid = candidate_data.get("sdpMid", "")
            ice.sdpMLineIndex = candidate_data.get("sdpMLineIndex", 0)
            await self.peer_connections[viewer_id].addIceCandidate(ice)
        except Exception as e:
            logger.error(f"Error adding ICE candidate: {e}")

    async def handle_client_left(self, client_id: str) -> None:
        """Handle a client disconnection."""
        if client_id in self.peer_connections:
            await self.peer_connections[client_id].close()
            del self.peer_connections[client_id]

    async def cleanup(self) -> None:
        """Close all peer connections."""
        for pc in list(self.peer_connections.values()):
            await pc.close()

        for pc in list(self.peer_connections.values()):
            for sender in pc.getSenders():
                if sender.track and isinstance(sender.track, PiCameraTrack):
                    pass

        self.peer_connections.clear()

    def get_connections_count(self) -> int:
        """Get the number of active connections."""
        return len(self.peer_connections)
