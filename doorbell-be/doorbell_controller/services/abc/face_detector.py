from abc import ABC, abstractmethod

class IFaceDetector(ABC):

    @abstractmethod
    def detect_from_file(self, path: str):
        pass
