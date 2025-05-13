import os
import asyncio
from asyncio import Lock, Task, CancelledError, wait_for, create_task, Queue
from datetime import datetime
from logging import getLogger
from typing import Dict, Any, Optional

from picamera2 import Picamera2

from doorbell_controller import SensorEvent, Event, Capture
from doorbell_controller.services import ICamera, IFaceDetector
from ..webrtc import WebRTCManager


class CameraService(ICamera):

    def __init__(
        self,
        config: Dict[str, Any],
        event_queue: Queue[Event[SensorEvent]],
        capture_queue: Queue[Capture],
        face_detector: IFaceDetector,
        token: str,
        signaling_server: str,
        signaling_ws
    ):
        self.config = config
        self.picam2 = None

        self._current_event = None
        self._face_detector = face_detector
        self._event_queue = event_queue
        self._capture_queue = capture_queue
        self._lock = Lock()
        self._stop_motion_task: Optional[Task] = None
        self._end_stop_motion_event = asyncio.Event()
        self._streaming = False

        self.webrtc_config = self.config.get("webrtc", {})
        self._room_id = self.webrtc_config.get("room_id", "camera-room-1")
        self._signaling_server = signaling_server
        self._signaling_ws = signaling_ws
        self._auth_token = token
        self.webrtc_manager = None

        stop_motion_conf = self.config.get("stop_motion", {})
        self._OUTPUT_DIR = stop_motion_conf.get("output_dir", "stop_motion")
        self._interval = stop_motion_conf.get("interval", 1.0)

        self._logger = getLogger(__name__)

        self._setup_camera()

    @property
    async def interval(self) -> float:
        async with self._lock:
            return self._interval

    @interval.setter
    async def interval(self, value: float):
        async with self._lock:
            if value <= 0:
                raise ValueError("Interval between stop motion captures must be positive")
            self._interval = value

    def _setup_camera(self):
        self._logger.debug("Setting up camera...")
        try:
            resolution = self.config.get("resolution", {"width": 1280, "height": 720})

            self.picam2 = Picamera2()
            config = self.picam2.create_video_configuration(
                main={
                    "size": (resolution["width"], resolution["height"]),
                    "format": self.config.get("format", "YUV420")
                },
                controls={
                    "FrameRate": self.config.get("framerate", 30)
                }
            )
            self.picam2.configure(config)
            self.picam2.start()

            self.webrtc_manager = WebRTCManager(self.picam2, self._signaling_ws)

            self._logger.debug("Camera setup completed successfully")
        except Exception as e:
            self._logger.error(f"Failed to setup camera: {str(e)}")
            raise

    async def start_stream(self) -> Optional[str]:
        async with self._lock:
            if self._streaming:
                self._logger.debug("Stream start request, stream already running...")
                status = await self.webrtc_manager.get_streaming_status()
                return f"WebRTC stream active with {status['connections']} viewer(s)"

            self._logger.debug("Starting WebRTC stream...")

            try:
                success = await self.webrtc_manager.start_streaming(
                    self._signaling_server,
                    self._room_id,
                    self._auth_token
                )

                if success:
                    self._streaming = True
                    self._logger.debug("WebRTC stream started successfully")
                    return f"WebRTC stream available in room: {self._room_id}"
                else:
                    self._logger.error("Failed to start WebRTC stream")
                    return None
            except Exception as e:
                self._logger.error(f"Error starting WebRTC stream: {str(e)}")
                return None

    async def stop_stream(self) -> bool:
        async with self._lock:
            if not self._streaming:
                self._logger.debug("Stop stream request, but no stream is running")
                return False

            self._logger.debug("Stopping WebRTC stream...")
            try:
                success = await self.webrtc_manager.stop_streaming()
                if success:
                    self._streaming = False
                    return True
                return False
            except Exception as e:
                self._logger.error(f"Error stopping WebRTC stream: {str(e)}")
                return False

    async def begin_stop_motion(self, e_id: str = None) -> bool:
        async with self._lock:
            if e_id is None:
                e_id = f"event_{int(datetime.now().timestamp())}"

            self._current_event = e_id
            self._logger.debug("Starting stop motion...")
            try:
                if self._stop_motion_task and not self._stop_motion_task.done():
                    self._logger.debug("Stopping existing stop motion task")
                    self._end_stop_motion_event.set()
                    await wait_for(self._stop_motion_task, timeout=5)

                self._end_stop_motion_event.clear()
                self._stop_motion_task = create_task(self._stop_motion_loop())
                return True
            except Exception as e:
                self._logger.error(f"Error starting stop motion: {str(e)}")
                return False

    async def end_stop_motion(self):
        async with self._lock:
            self._logger.debug("Stopping stop motion...")
            if not self._stop_motion_task or self._stop_motion_task.done():
                self._logger.debug("No stop motion task running")
                return True
            try:
                self._end_stop_motion_event.set()
                await wait_for(self._stop_motion_task, timeout=5)
                return True
            except asyncio.TimeoutError:
                self._logger.warning("Stop motion task did not end gracefully, cancelling...")
                self._stop_motion_task.cancel()
                try:
                    await self._stop_motion_task
                except CancelledError:
                    pass
                return True
            except Exception as e:
                self._logger.error(f"Error stopping stop motion: {str(e)}")
                return False
            finally:
                self._stop_motion_task = None
                return None

    async def _stop_motion_loop(self):
        frame_count = 0

        try:
            os.makedirs(self._OUTPUT_DIR, exist_ok=True)

            while not self._end_stop_motion_event.is_set():
                timestamp = int(datetime.now().timestamp())
                filename = f"{self._current_event}_{frame_count:05d}_{timestamp}.jpg"
                filepath = os.path.join(self._OUTPUT_DIR, filename)

                try:
                    async with self._lock:
                        self.picam2.capture_file(filepath)
                        has_face = self._face_detector.detect_from_file(filepath)
                        if has_face:
                            event = Event(
                                type=SensorEvent.FACE_DETECTED,
                                timestamp=datetime.now()
                            )
                            await self._event_queue.put(event)
                        await self._capture_queue.put(Capture(
                            path=filename,
                            associated_to=self._current_event
                        ))
                except Exception as e:
                    self._logger.error(f"Error capturing frame: {str(e)}")
                    continue

                self._logger.debug(f"Captured frame {frame_count + 1}: {filename}")
                frame_count += 1

                try:
                    await wait_for(
                        self._end_stop_motion_event.wait(),
                        timeout=self._interval
                    )
                    break
                except asyncio.TimeoutError:
                    continue

        except Exception as e:
            self._logger.error(f"Error in recording loop: {str(e)}")
        finally:
            self._logger.debug(f"Recording stopped. Total frames: {frame_count}")

    async def get_streaming_status(self):
        if self.webrtc_manager:
            return await self.webrtc_manager.get_streaming_status()
        return {"active": False}

    async def cleanup(self):
        self._logger.debug("Cleaning up camera resources...")
        try:
            await self.end_stop_motion()
            await self.stop_stream()

            if self.picam2:
                try:
                    self.picam2.stop()
                    self.picam2.close()
                    self.picam2 = None
                except Exception as e:
                    self._logger.error(f"Error closing camera: {str(e)}")
        except Exception as e:
            self._logger.error(f"Error during camera cleanup: {str(e)}")
            raise
