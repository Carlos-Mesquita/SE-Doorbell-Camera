import os
import asyncio
import subprocess
from datetime import datetime
from logging import getLogger
from typing import Dict, Any, Optional, Tuple

from picamera2 import Picamera2  # type: ignore
from picamera2.encoders import H264Encoder  # type: ignore

from doorbell_controller.services import ICamera


class CameraService(ICamera):

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.picam2 = None
        self.gst_process = None
        self.encoder = None

        self._lock = asyncio.Lock()
        self._stop_motion_task: Optional[asyncio.Task] = None
        self._end_stop_motion_event = asyncio.Event()
        self._streaming = False

        streaming_conf = self.config.get("streaming", {})
        self._HOST = streaming_conf.get("host", "localhost")
        self._PORT = streaming_conf.get("port", 8554)
        self._bitrate = streaming_conf.get("bitrate", 2_000_000)

        stop_motion_conf = self.config.get("stop_motion", {})
        self._OUTPUT_DIR = stop_motion_conf.get("output_dir", "stop_motion")
        self._interval = stop_motion_conf.get("interval", 1.0)

        self._logger = getLogger(__name__)

        self._setup_camera()

    @property
    def bitrate(self) -> int:
        return self._bitrate

    @bitrate.setter
    def bitrate(self, value: int):
        if value < 1_000_000:
            raise ValueError("Bitrate must be at least 1 Mbps for 720p@30fps")
        self._bitrate = value

    @property
    def interval(self) -> float:
        return self._interval

    @interval.setter
    def interval(self, value: float):
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
            self._logger.debug("Camera setup completed successfully")
        except Exception as e:
            self._logger.error(f"Failed to setup camera: {str(e)}")
            raise

    async def start_stream(self) -> Optional[str]:
        async with self._lock:
            if self._streaming:
                self._logger.debug("Stream start request, stream already running...")
                return f"rtsp://{self._HOST}:{self._PORT}/stream"

            self._logger.debug("Starting stream...")
            try:
                if os.path.exists('camera_pipe'):
                    os.remove('camera_pipe')
                os.mkfifo('camera_pipe')

                gst_command = [
                    'gst-launch-1.0',
                    'filesrc', 'location=camera_pipe', '!',
                    'h264parse', '!',
                    'rtspclientsink',
                    f'location=rtsp://0.0.0.0:{self._PORT}/stream'
                ]

                self.gst_process = subprocess.Popen(gst_command)
                self.encoder = H264Encoder(
                    bitrate=self._bitrate
                )
                self.picam2.start_recording(self.encoder, 'camera_pipe')

                self._streaming = True
                self._logger.debug("Stream started successfully")
                return f"rtsp://{self._HOST}:{self._PORT}/stream"

            except Exception as e:
                self._logger.error(f"Error starting stream: {str(e)}")
                await self._cleanup_stream()
                return None

    async def stop_stream(self) -> bool:
        async with self._lock:
            if not self._streaming:
                self._logger.debug("Stop stream request, but no stream is running")
                return False

            self._logger.debug("Stopping stream...")
            try:
                await self._cleanup_stream()
                return True
            except Exception as e:
                self._logger.error(f"Error stopping stream: {str(e)}")
                return False

    async def _cleanup_stream(self):
        if self._streaming:
            self._logger.debug("Cleaning up stream resources...")
            try:
                self.picam2.stop_recording()
                if self.gst_process:
                    self.gst_process.terminate()
                    self.gst_process.wait()
                if os.path.exists('camera_pipe'):
                    os.remove('camera_pipe')
            except Exception as e:
                self._logger.error(f"Error during stream cleanup: {str(e)}")
                raise
            finally:
                self._streaming = False
                self.gst_process = None
                self.encoder = None

    async def begin_stop_motion(self) -> bool:
        async with self._lock:
            self._logger.debug("Starting stop motion...")
            try:
                if self._stop_motion_task and not self._stop_motion_task.done():
                    self._end_stop_motion_event.set()
                    await self._stop_motion_task

                self._end_stop_motion_event.clear()
                self._stop_motion_task = asyncio.create_task(self._stop_motion_loop())
                return True
            except Exception as e:
                self._logger.error(f"Error starting stop motion: {str(e)}")
                return False

    async def end_stop_motion(self):
        async with self._lock:
            self._logger.debug("Stopping stop motion...")
            try:
                if self._stop_motion_task and not self._stop_motion_task.done():
                    self._end_stop_motion_event.set()
                    await self._stop_motion_task
                return True
            except Exception as e:
                self._logger.error(f"Error stopping stop motion: {str(e)}")
                return False
            finally:
                self._stop_motion_task = None

    async def _stop_motion_loop(self):
        frame_count = 0

        try:
            os.makedirs(self._OUTPUT_DIR, exist_ok=True)

            while not self._end_stop_motion_event.is_set():
                timestamp = int(datetime.now().timestamp())
                filename = f"frame_{frame_count:05d}_{timestamp}.jpg"
                filepath = os.path.join(self._OUTPUT_DIR, filename)

                async with self._lock:
                    self.picam2.capture_file(filepath)

                self._logger.debug(f"Captured frame {frame_count + 1}: {filename}")
                frame_count += 1

                try:
                    await asyncio.wait_for(
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

    async def cleanup(self):
        self._logger.debug("Cleaning up camera resources...")
        try:
            await self.end_stop_motion()
            await self._cleanup_stream()
            if self.picam2:
                self.picam2.stop()
                self.picam2.close()
        except Exception as e:
            self._logger.error(f"Error during camera cleanup: {str(e)}")
