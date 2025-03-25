import datetime
from typing import TypeVar, List, Dict, Any, Generic, Optional
from pydantic import BaseModel

from doorbell_api.mappers.abc import IMapper
from doorbell_api.repositories import IBaseRepository
from doorbell_api.services import IBaseService
from doorbell_api.configs.db import Base, Transactional

TDTO = TypeVar('TDTO', bound=BaseModel)
TModel = TypeVar('TModel', bound=Base)
TRepository = TypeVar('TRepository', bound=IBaseRepository)


class BaseService(IBaseService[TDTO, TModel], Generic[TDTO, TModel]):

    def __init__(self, mapper: IMapper[TDTO, TModel], repo: IBaseRepository[TModel]):
        self._mapper = mapper
        self._repo = repo

    async def get_all(self, **data: Dict[str, any]) -> List[TDTO]:
        models = await self._repo.get_all_models(**data)
        return [self._mapper.to_dto(model) for model in models]

    async def get_by_id(self, model_id: int) -> TDTO:
        model = await self._repo.get_model_by_id(model_id)
        return self._mapper.to_dto(model)

    @Transactional()
    async def create(self, dto: TDTO) -> TDTO:
        model = self._mapper.to_orm(dto)
        new_model = await self._repo.create_model(model)
        return self._mapper.to_dto(new_model)

    @Transactional()
    async def update_by_id(self, model_id: int, dto: TDTO) -> TDTO:
        kwargs = self._mapper.dto_kwargs(dto)
        kwargs.pop('id', None)
        kwargs.pop('created_at', None)
        kwargs['updated_at'] = datetime.datetime.now()
        updated_model = await self._repo.update_model_by_id(model_id, kwargs)
        return self._mapper.to_dto(updated_model)

    @Transactional()
    async def delete_by_id(self, model_id: int) -> None:
        await self._repo.delete_model_by_id(model_id)

    @Transactional()
    async def delete_by_ids(self, model_ids: List[int]) -> int:
        return await self._repo.delete_models_by_ids(model_ids)

    async def count_all(self, filter_by: Optional[Dict[str, Any]] = None) -> int:
        return await self._repo.count_hits(filter_by=filter_by)
