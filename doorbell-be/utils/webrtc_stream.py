import asyncio, json, logging, argparse, uuid, websockets, hmac, hashlib, base64, time, av
from fractions import Fraction
from aiortc import VideoStreamTrack, RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription
from aiortc.sdp import candidate_from_sdp
from picamera2 import Picamera2
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

peer_connections = {}
client_id = None
websocket = None
current_viewer_id = None

class PiCameraTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, width=1280, height=720, framerate=10):
        super().__init__()
        self.picam2 = None
        self.width = width
        self.height = height
        self.framerate = framerate
        self.initialize_camera()

    def initialize_camera(self):
        try:
            if self.picam2:
                try:
                    self.picam2.stop()
                    self.picam2.close()
                except:
                    pass

            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={"size": (self.width, self.height), "format": "YUV420"},
                buffer_count=2,
                controls={
                    "FrameRate": self.framerate,
                    "NoiseReductionMode": 0,
                    "AwbMode": 0
                }
            )
            self.picam2.configure(config)
            self.picam2.start()
            logger.info(f"PiCamera2 initialized at {self.width}x{self.height} @ {self.framerate}fps")
            return True
        except Exception as e:
            logger.error(f"Camera initialization failed: {e}")
            return False

    async def recv(self):
        if not self.picam2:
            if not self.initialize_camera():
                frame = av.VideoFrame(width=self.width, height=self.height, format="yuv420p")
                frame.pts = int(time.time() * 1000000)
                frame.time_base = Fraction(1, 1000000)
                return frame

        pts = int(time.time() * 1000000)
        try:
            img = self.picam2.capture_array()
            frame = av.VideoFrame.from_ndarray(img, format="yuv420p")
            frame.pts = pts
            frame.time_base = Fraction(1, 1000000)
            return frame
        except Exception as e:
            logger.error(f"Error capturing frame: {str(e)}")
            frame = av.VideoFrame(width=self.width, height=self.height, format="yuv420p")
            frame.pts = pts
            frame.time_base = Fraction(1, 1000000)
            return frame

    def stop(self):
        if hasattr(self, 'picam2') and self.picam2:
            try:
                self.picam2.stop()
                self.picam2.close()
                self.picam2 = None
                logger.info("PiCamera2 stopped and closed")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")

def create_credential(username_base, secret):
    expiry = int(time.time()) + 24 * 3600
    username_with_expiry = f"{expiry}:{username_base}"
    hmac_obj = hmac.new(secret.encode(), username_with_expiry.encode(), hashlib.sha1)
    credential = base64.b64encode(hmac_obj.digest()).decode()
    return username_with_expiry, credential

def create_peer_connection():
    global client_id, websocket, current_viewer_id

    turn_host = os.getenv("TURN_HOST")
    turn_secret = os.getenv("TURN_SECRET")
    username_with_expiry, credential = create_credential(client_id or "broadcaster", turn_secret)

    pc = RTCPeerConnection(
        configuration=RTCConfiguration(
            iceServers=[
                RTCIceServer(f"turns:{turn_host}:5349?transport=tcp", username_with_expiry, credential),
                RTCIceServer(f"turn:{turn_host}:3478?transport=udp", username_with_expiry, credential)
            ],
        )
    )

    @pc.on("icecandidate")
    async def on_icecandidate(candidate):
        if candidate and websocket and current_viewer_id:
            await websocket.send(json.dumps({
                "type": "ice-candidate", "clientId": client_id, "target": current_viewer_id,
                "candidate": {
                    "candidate": candidate.candidate,
                    "sdpMid": candidate.sdpMid,
                    "sdpMLineIndex": candidate.sdpMLineIndex,
                }
            }))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        logger.info(f"Connection state is {pc.connectionState}")
        if pc.connectionState == "failed" and current_viewer_id in peer_connections:
            del peer_connections[current_viewer_id]
            await pc.close()

    video = PiCameraTrack()
    pc.addTrack(video)

    return pc

async def process_signaling(ws_url, room_id, auth_token):
    global client_id, peer_connections, websocket, current_viewer_id

    try:
        async with websockets.connect(f"{ws_url}?token={auth_token}") as ws:
            websocket = ws
            reg_data = json.loads(await ws.recv())

            if reg_data.get("type") == "registered":
                client_id = reg_data.get("clientId")
                logger.info(f"Registered as: {client_id}")

                await ws.send(json.dumps({
                    "type": "join", "clientId": client_id, "roomId": room_id, "role": "broadcaster"
                }))

                while True:
                    try:
                        data = json.loads(await ws.recv())
                        msg_type = data.get("type")

                        if msg_type == "offer" and (data.get("target") == client_id or data.get("target") == "broadcaster"):
                            viewer_id = data.get("clientId")
                            current_viewer_id = viewer_id

                            if viewer_id in peer_connections:
                                await peer_connections[viewer_id].close()

                            peer_connections[viewer_id] = create_peer_connection()
                            pc = peer_connections[viewer_id]

                            sdp = data.get("sdp")
                            if not sdp:
                                continue

                            offer = RTCSessionDescription(sdp=sdp, type="offer")
                            await pc.setRemoteDescription(offer)
                            answer = await pc.createAnswer()
                            await pc.setLocalDescription(answer)

                            await ws.send(json.dumps({
                                "type": "answer", "clientId": client_id, "target": viewer_id,
                                "sdp": pc.localDescription.sdp
                            }))

                        elif msg_type == "ice-candidate" and (data.get("target") == client_id or data.get("target") == "broadcaster"):
                            viewer_id = data.get("clientId")
                            candidate_data = data.get("candidate")

                            if viewer_id in peer_connections and candidate_data:
                                try:
                                    candidate_str = candidate_data.get("candidate", "")
                                    if candidate_str.startswith("candidate:"):
                                        candidate_str = candidate_str[10:]

                                    ice = candidate_from_sdp(candidate_str)
                                    ice.sdpMid = candidate_data.get("sdpMid", "")
                                    ice.sdpMLineIndex = candidate_data.get("sdpMLineIndex", 0)
                                    await peer_connections[viewer_id].addIceCandidate(ice)
                                except Exception as e:
                                    logger.error(f"Error adding ICE candidate: {e}")

                        elif msg_type == "client-left":
                            departed_id = data.get("clientId")
                            if departed_id in peer_connections:
                                await peer_connections[departed_id].close()
                                del peer_connections[departed_id]

                    except websockets.exceptions.ConnectionClosed:
                        break
                    except Exception as e:
                        logger.error(f"Signaling error: {e}")
            else:
                logger.error(f"Registration failed: {reg_data}")

    except Exception as e:
        logger.error(f"Connection error: {e}")
        await asyncio.sleep(5)
        asyncio.create_task(process_signaling(ws_url, room_id, auth_token))

async def cleanup():
    for pc in peer_connections.values():
        await pc.close()

    for pc in peer_connections.values():
        for sender in pc.getSenders():
            if sender.track and isinstance(sender.track, PiCameraTrack):
                sender.track.stop()

    peer_connections.clear()

async def main(signaling_uri, room_id, token):
    try:
        await process_signaling(signaling_uri, room_id, token)
    except KeyboardInterrupt:
        pass
    finally:
        await cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PiCamera2 WebRTC Server")
    parser.add_argument("--server", required=True, help="WebSocket URI (ws://host:port/path)")
    parser.add_argument("--room", default="camera-room-1", help="Room ID to join")
    parser.add_argument("--token", required=True, help="Auth token")

    parser.add_argument("--width", type=int, default=640, help="Video width (default: 640)")
    parser.add_argument("--height", type=int, default=480, help="Video height (default: 480)")
    parser.add_argument("--fps", type=int, default=15, help="Framerate (default: 15)")

    args = parser.parse_args()

    if args.width != 640 or args.height != 480 or args.fps != 15:
        PiCameraTrack.__init__ = lambda self, width=args.width, height=args.height, framerate=args.fps: (
            VideoStreamTrack.__init__(self),
            setattr(self, 'width', width),
            setattr(self, 'height', height),
            setattr(self, 'framerate', framerate),
            setattr(self, 'picam2', None),
            self.initialize_camera()
        )[-1]

    logger.info(f"Starting camera: {args.width}x{args.height} @ {args.fps}fps")
    asyncio.run(main(args.server, args.room, args.token))
