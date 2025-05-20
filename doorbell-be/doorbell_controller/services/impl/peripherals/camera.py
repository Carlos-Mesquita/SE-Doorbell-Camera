import io
import os
import asyncio
from asyncio import Lock, Task, CancelledError, wait_for, create_task, Queue
from datetime import datetime
from logging import getLogger
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from uuid import uuid4

from picamera2 import Picamera2  # type: ignore

from doorbell_controller.models import SensorEvent, Event, Capture
from doorbell_controller.services import ICameraService, IFaceDetector
from ..webrtc import WebRTCManager


class CameraService(ICameraService):

    def __init__(
            self,
            config: Dict[str, Any],
            event_queue: Queue[Event[SensorEvent]],
            capture_queue: Queue[Capture],
            face_detector: IFaceDetector,
            auth_token: str,
            signaling_server_url: str
    ):
        self.config = config
        self.picam2: Optional[Picamera2] = None
        self._current_event_id: Optional[str] = None
        self._face_detector = face_detector
        self._event_queue = event_queue
        self._capture_queue = capture_queue
        self._lock = Lock()
        self._stop_motion_task: Optional[Task] = None
        self._end_stop_motion_event = asyncio.Event()
        self._is_streaming = False
        self.webrtc_config = self.config.get("webrtc", {})
        self._room_id = self.webrtc_config.get("room_id", "default-doorbell-room")
        self._signaling_server_url = signaling_server_url
        self._auth_token = auth_token
        self.turn_settings = self.webrtc_config.get("turn_server", {})
        self.webrtc_manager: Optional[WebRTCManager] = None
        stop_motion_conf = self.config.get("stop_motion", {})
        self._OUTPUT_DIR = Path(stop_motion_conf.get("output_dir", "stop_motion_captures"))
        self._stop_motion_interval_seconds = float(stop_motion_conf.get("interval_seconds", 1.0))
        self._logger = getLogger(__name__)
        self._setup_camera()


    @property
    async def stop_motion_interval(self) -> float:
        async with self._lock:
            return self._stop_motion_interval_seconds


    async def set_stop_motion_interval(self, value: float):
        async with self._lock:
            if value <= 0:
                self._logger.error("Stop motion interval must be positive.")
                raise ValueError("Interval between stop motion captures must be positive")
            old_interval = self._stop_motion_interval_seconds
            self._stop_motion_interval_seconds = value
            self._logger.info(f"Stop motion interval changed from {old_interval}s to {value}s.")


    def _setup_camera(self):
        self._logger.info("Setting up camera...")
        try:
            resolution_config = self.config.get("resolution", {"width": 1280, "height": 720})
            width = int(resolution_config.get("width", 1280))
            height = int(resolution_config.get("height", 720))
            framerate = int(self.config.get("framerate", 30))
            camera_format = self.config.get("format", "YUV420")
            self.picam2 = Picamera2()
            video_config = self.picam2.create_video_configuration(
                main={"size": (width, height), "format": camera_format},
                controls={"FrameRate": float(framerate)}
            )
            self.picam2.configure(video_config)
            self._configured_resolution = (width, height)
            self.picam2.start()
            self.webrtc_manager = WebRTCManager(self.picam2, self.turn_settings)
            self._OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            self._logger.info(f"Camera setup completed. Captures will be saved to: {self._OUTPUT_DIR.resolve()}")

        except ImportError:
            self._logger.error("Picamera2 library not found. Camera functionality will be disabled.", exc_info=True)
            self.picam2 = None
            self.webrtc_manager = None
        except Exception as e:
            self._logger.error(f"Failed to setup camera: {str(e)}", exc_info=True)
            self.picam2 = None
            self.webrtc_manager = None



    async def start_stream(self) -> Optional[str]:
        if not self.picam2 or not self.webrtc_manager:
            self._logger.warning("Cannot start stream: Camera or WebRTC manager not initialized.")
            return None

        async with self._lock:
            if self._is_streaming:
                self._logger.info("Stream start request, but stream is already running.")
                status = await self.webrtc_manager.get_streaming_status()
                return f"WebRTC stream already active in room: {status.get('room_id', self._room_id)}"

            self._logger.info("Attempting to start WebRTC stream...")
            try:

                success = await self.webrtc_manager.start_streaming(
                    self._signaling_server_url,
                    self._room_id,
                    self._auth_token
                )

                if success:
                    self._is_streaming = True
                    self._logger.info(f"WebRTC stream started successfully for room: {self._room_id}")

                    return f"room:{self._room_id}"
                else:
                    self._logger.error("Failed to start WebRTC stream (WebRTCManager indicated failure).")
                    self._is_streaming = False
                    return None
            except Exception as e:
                self._logger.error(f"Exception starting WebRTC stream: {str(e)}", exc_info=True)
                self._is_streaming = False
                return None

    async def stop_stream(self) -> bool:
        if not self.webrtc_manager:
            self._logger.warning("Cannot stop stream: WebRTC manager not initialized.")
            return False

        async with self._lock:
            if not self._is_streaming:
                self._logger.info("Stop stream request, but no stream is running.")
                return True

            self._logger.info("Attempting to stop WebRTC stream...")
            try:
                success = await self.webrtc_manager.stop_streaming()
                if success:
                    self._is_streaming = False
                    self._logger.info("WebRTC stream stopped successfully.")
                    return True
                else:
                    self._logger.error("Failed to stop WebRTC stream (WebRTCManager indicated failure).")


                    return False
            except Exception as e:
                self._logger.error(f"Exception stopping WebRTC stream: {str(e)}", exc_info=True)
                return False

    async def begin_stop_motion(self, event_id: Optional[str] = None) -> bool:
        if not self.picam2:
            self._logger.warning("Cannot begin stop motion: Camera not initialized.")
            return False

        async with self._lock:
            if self._is_streaming:
                self._logger.warning("Cannot begin stop motion while WebRTC streaming is active.")
                return False

            if self._stop_motion_task and not self._stop_motion_task.done():
                self._logger.info("Stop motion already in progress. Resetting with new event ID if provided.")
                if event_id:
                    self._current_event_id = event_id
                return True

            self._current_event_id = event_id if event_id else f"event_{int(datetime.now().timestamp())}"
            self._logger.info(f"Starting stop motion for event ID: {self._current_event_id}")

            self._end_stop_motion_event.clear()
            self._stop_motion_task = create_task(self._stop_motion_loop(), name=f"StopMotion_{self._current_event_id}")
            return True

    async def end_stop_motion(self) -> bool:
        async with self._lock:
            if not self._stop_motion_task or self._stop_motion_task.done():
                self._logger.info("End stop motion called, but no task running or already finished.")
                self._stop_motion_task = None
                return True

            self._logger.info("Attempting to end stop motion...")
            self._end_stop_motion_event.set()

            try:
                await wait_for(self._stop_motion_task, timeout=5.0)
                self._logger.info("Stop motion task ended gracefully.")
            except asyncio.TimeoutError:
                self._logger.warning("Stop motion task did not end gracefully on signal, cancelling...")
                self._stop_motion_task.cancel()
                try:
                    await self._stop_motion_task
                except CancelledError:
                    self._logger.info("Stop motion task successfully cancelled.")

            except Exception as e:
                self._logger.error(f"Unexpected error waiting for stop motion task: {e}", exc_info=True)
            finally:
                self._stop_motion_task = None
                self._current_event_id = None
        return True

    async def _stop_motion_loop(self):
        frame_count = 0
        if not self.picam2: return

        self._OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        current_loop_event_id = self._current_event_id
        self._logger.info(
            f"Stop motion loop started for event ID: {current_loop_event_id}. Interval: {self._stop_motion_interval_seconds}s.")

        try:
            while not self._end_stop_motion_event.is_set():
                loop_start_time = asyncio.get_event_loop().time()
                timestamp = datetime.now()

                image_bytes: Optional[bytes] = None
                temp_filepath_for_face_detection: Optional[Path] = None

                try:
                    with io.BytesIO() as stream:
                        await asyncio.to_thread(self.picam2.capture_file, stream, format='jpeg')
                        stream.seek(0)
                        image_bytes = stream.read()

                    self._logger.debug(f"Captured frame {frame_count + 1} to memory for event {current_loop_event_id}")
                    frame_count += 1

                    has_face = False
                    if image_bytes:
                        temp_filename = f"temp_face_detect_{uuid4()}.jpg"
                        temp_filepath_for_face_detection = self._OUTPUT_DIR / temp_filename
                        with open(temp_filepath_for_face_detection, 'wb') as f_temp:
                            f_temp.write(image_bytes)

                        has_face = await asyncio.to_thread(self._face_detector.detect_from_file,
                                                           str(temp_filepath_for_face_detection))

                        try:
                            os.remove(temp_filepath_for_face_detection)
                        except OSError as e:
                            self._logger.warning(
                                f"Could not remove temporary face detection file {temp_filepath_for_face_detection}: {e}")

                    if has_face:
                        self._logger.info(f"Face detected in captured frame for event {current_loop_event_id}")
                        face_event = Event[SensorEvent](
                            type=SensorEvent.FACE_DETECTED,
                            timestamp=timestamp,
                            payload={'event_id_for_capture': current_loop_event_id,
                                     'notes': 'Face detected in memory capture'},
                        )
                        await self._event_queue.put(face_event)

                    if image_bytes:
                        capture_info = Capture(
                            associated_to=str(current_loop_event_id),
                            timestamp=timestamp,
                            image_data=image_bytes,
                            image_format="jpeg",
                            has_face=has_face
                        )
                        await self._capture_queue.put(capture_info)

                except Exception as e:
                    self._logger.error(f"Error capturing/processing frame to memory: {str(e)}", exc_info=True)
                finally:
                    if temp_filepath_for_face_detection and os.path.exists(temp_filepath_for_face_detection):
                        try:  # Ensure cleanup even if other parts fail
                            os.remove(temp_filepath_for_face_detection)
                        except OSError as e:
                            self._logger.warning(
                                f"Could not remove temporary face detection file {temp_filepath_for_face_detection} in finally: {e}")

                try:

                    elapsed_time = asyncio.get_event_loop().time() - loop_start_time
                    sleep_duration = self._stop_motion_interval_seconds - elapsed_time
                    if sleep_duration < 0: sleep_duration = 0

                    if sleep_duration > 0:
                        await wait_for(self._end_stop_motion_event.wait(), timeout=sleep_duration)


                    if self._end_stop_motion_event.is_set():
                        self._logger.info("Stop motion loop: stop event detected during interval wait.")
                        break
                except asyncio.TimeoutError:
                    pass
                except CancelledError:
                    self._logger.info("Stop motion loop task directly cancelled.")
                    raise

        except CancelledError:
            self._logger.info(f"Stop motion loop for {current_loop_event_id} was cancelled.")
        except Exception as e:
            self._logger.error(f"Unhandled error in stop motion loop for {current_loop_event_id}: {str(e)}",
                               exc_info=True)
        finally:
            self._logger.info(
                f"Stop motion loop for event ID {current_loop_event_id} finished. Total frames: {frame_count}")

    async def get_streaming_status(self) -> Dict[str, Any]:
        if self.webrtc_manager:
            return await self.webrtc_manager.get_streaming_status()
        return {"active": False, "connections": 0, "client_id": None, "room_id": None}

    async def get_stop_motion_interval(self) -> float:
        return self._stop_motion_interval_seconds

    async def cleanup(self):
        self._logger.info("Cleaning up camera service resources...")

        if self._stop_motion_task and not self._stop_motion_task.done():
            await self.end_stop_motion()
        if self._is_streaming:
            await self.stop_stream()

        if self.webrtc_manager:
            await self.webrtc_manager.stop_streaming()
            self.webrtc_manager = None

        if self.picam2:
            try:
                self._logger.info("Stopping Picamera2 instance...")
                self.picam2.stop()
                self._logger.info("Picamera2 instance stopped.")
            except Exception as e:
                self._logger.error(f"Error stopping/closing Picamera2: {str(e)}", exc_info=True)
            finally:
                self.picam2 = None
        self._logger.info("Camera service cleanup complete.")