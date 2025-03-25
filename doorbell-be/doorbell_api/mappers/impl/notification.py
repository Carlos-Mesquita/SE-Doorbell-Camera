from doorbell_api.dtos import NotificationDTO
from doorbell_api.models import Notification

from .base import Mapper


class NotificationMapper(Mapper[NotificationDTO, Notification]):
    def __init__(self):
        super().__init__(
            orm_model=Notification,
            dto_model=NotificationDTO,
            field_mapping={
                'id': 'id',
                'title': 'title',
                'created_at': 'created_at',
                'captures': 'captures'
            },
            exclude_dto_keys=set('id')
        )
