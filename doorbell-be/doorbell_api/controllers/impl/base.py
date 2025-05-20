from http import HTTPStatus
from typing import TypeVar, List, Dict, Generic, Any, Optional
from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound

from ...controllers import IBaseController
from ...dtos.hits import HitsDTO
from ...exceptions import CatchesAndThrows, NotFoundException
from ...services import IBaseService

TDTO = TypeVar('TDTO', bound=BaseModel)


class BaseController(IBaseController, Generic[TDTO]):
    NOT_FOUND_MESSAGE = HTTPStatus.NOT_FOUND.description

    def __init__(self, service: IBaseService):
        self._service = service

    async def get_all(self, **data: Dict[str, Any]) -> List[TDTO]:
        return await self._service.get_all(**data)

    @CatchesAndThrows(NoResultFound, NotFoundException, NOT_FOUND_MESSAGE)
    async def get_by_id(self, model_id: int) -> TDTO:
        return await self._service.get_by_id(model_id)

    async def create(self, dto: TDTO) -> TDTO:
        return await self._service.create(dto)

    @CatchesAndThrows(NoResultFound, NotFoundException, NOT_FOUND_MESSAGE)
    async def update_by_id(self, model_id: int, dto: TDTO) -> TDTO:
        return await self._service.update_by_id(model_id, dto)

    @CatchesAndThrows(NoResultFound, NotFoundException, NOT_FOUND_MESSAGE)
    async def delete_by_id(self, model_id: int) -> None:
        await self._service.delete_by_id(model_id)

    async def delete_by_ids(self, model_ids: List[int]) -> int:
        return await self._service.delete_by_ids(model_ids)

    async def count_all(self, filter_by: Optional[Dict[str, Any]] = None) -> HitsDTO:
        hits = await self._service.count_all(filter_by=filter_by)
        return HitsDTO(hits=hits)
