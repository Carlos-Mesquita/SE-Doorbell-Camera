import asyncio
import time
import logging
from fractions import Fraction

import av
from aiortc import VideoStreamTrack

logger = logging.getLogger(__name__)


class PiCameraTrack(VideoStreamTrack):
    kind = "video"

    def __init__(self, picam2, width=1280, height=720, framerate=10):
        super().__init__()
        self.picam2 = picam2
        self.width = width
        self.height = height
        self._initialized = self.picam2 is not None
        if not self._initialized:
            logger.warning("PiCameraTrack initialized without a Picamera2 instance. Will send blank frames.")
        self._task = None


    async def recv(self):
        pts = int(time.monotonic_ns() / 1000)
        time_base = Fraction(1, 1000000)

        if not self._initialized or not self.picam2:
            frame = av.VideoFrame(width=self.width, height=self.height, format="yuv420p")  # Common format
            frame.pts = pts
            frame.time_base = time_base
            return frame

        try:
            loop = asyncio.get_running_loop()
            img_array = await loop.run_in_executor(None, self.picam2.capture_array)

            frame = av.VideoFrame.from_ndarray(img_array, format="yuv420p")
            frame.pts = pts
            frame.time_base = time_base
            return frame
        except Exception as e:
            logger.error(f"Error capturing frame from PiCamera2: {str(e)}", exc_info=True)
            frame = av.VideoFrame(width=self.width, height=self.height, format="yuv420p")
            frame.pts = pts
            frame.time_base = time_base
            return frame
