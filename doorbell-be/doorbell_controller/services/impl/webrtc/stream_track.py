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
        self.framerate = framerate
        self._initialized = self.picam2 is not None

    async def recv(self):
        if not self._initialized or not self.picam2:
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
