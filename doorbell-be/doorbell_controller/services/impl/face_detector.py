import cv2
from logging import getLogger
from typing import Tuple

from doorbell_controller.services import IFaceDetector


# https://medium.com/geeky-bawa/face-detection-using-haar-cascade-classifier-in-python-using-opencv-97873fbf24ec
class FaceDetector(IFaceDetector):

    def __init__(
        self,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: Tuple[int, int] = (30, 30)
    ):
        self._logger = getLogger(__name__)

        self._scale_factor = scale_factor
        self._min_neighbors = min_neighbors
        self._min_size = min_size

        self._face_cascade = cv2.CascadeClassifier('./doorbell_controller/haarcascade_frontalface_default.xml')

        if self._face_cascade.empty():
            raise RuntimeError("Failed to load face cascade classifier")

        self._logger.info("Face detector initialized")

    def detect_from_file(self, filepath: str) -> bool:
        try:
            image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            if image is None:
                self._logger.error(f"Failed to read image file: {filepath}")
                return False

            faces = self._face_cascade.detectMultiScale(
                image,
                scaleFactor=self._scale_factor,
                minNeighbors=self._min_neighbors,
                minSize=self._min_size
            )

            return len(faces) > 0

        except Exception as e:
            self._logger.error(f"Error detecting faces from file: {str(e)}")
            return False
