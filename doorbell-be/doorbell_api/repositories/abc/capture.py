from abc import ABC

from doorbell_api.dtos import CaptureDTO
from doorbell_api.models import Capture
from doorbell_api.services import IBaseService


class ICaptureService(IBaseService[CaptureDTO, Capture], ABC):
    pass
