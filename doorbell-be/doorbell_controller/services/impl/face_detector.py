import cv2 # type: ignore
from logging import getLogger
from typing import Tuple
from pathlib import Path

from doorbell_controller.services import IFaceDetector


class FaceDetector(IFaceDetector):

    def __init__(
        self,
        cascade_file_path: Path,
        scale_factor: float = 1.1,
        min_neighbors: int = 5,
        min_size: Tuple[int, int] = (30, 30)
    ):
        self._logger = getLogger(__name__)

        self._scale_factor = scale_factor
        self._min_neighbors = min_neighbors
        self._min_size = min_size


        if not cascade_file_path.is_file(): # Use the passed path
            msg = f"Haar cascade file not found at: {cascade_file_path}"
            self._logger.error(msg)
            raise RuntimeError(msg)

        self._face_cascade = cv2.CascadeClassifier(str(cascade_file_path))

        if self._face_cascade.empty():
            msg = f"Failed to load face cascade classifier from {cascade_file_path}"
            self._logger.error(msg)
            raise RuntimeError(msg)

        self._logger.info("Face detector initialized")

    def detect_from_file(self, filepath: str) -> bool:
        """
        Detects faces from an image file.
        filepath: Absolute or relative path to the image file.
        Returns: True if at least one face is detected, False otherwise.
        """
        if not Path(filepath).is_file():
            self._logger.error(f"Image file not found for face detection: {filepath}")
            return False

        try:
            image = cv2.imread(filepath, cv2.IMREAD_GRAYSCALE)
            if image is None:
                self._logger.error(f"Failed to read image file (cv2.imread returned None): {filepath}")
                return False

            faces = self._face_cascade.detectMultiScale(
                image,
                scaleFactor=self._scale_factor,
                minNeighbors=self._min_neighbors,
                minSize=self._min_size
            )

            return len(faces) > 0

        except Exception as e:
            self._logger.error(f"Error detecting faces from file '{filepath}': {str(e)}", exc_info=True)
            return False