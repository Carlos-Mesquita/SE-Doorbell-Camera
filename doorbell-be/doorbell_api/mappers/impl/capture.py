from doorbell_api.models import Capture
from doorbell_api.dtos import CaptureDTO

from .base import Mapper

class CaptureMapper(Mapper[CaptureDTO, Capture]):
    def __init__(self):
        super().__init__(
            orm_model=Capture,
            dto_model=CaptureDTO,
            field_mapping={
                'id': 'id',
                'notification_id': 'notification_id',
                'path': 'path',
                'created_at': 'created_at'
            },
            exclude_dto_keys=set('id')
        )
