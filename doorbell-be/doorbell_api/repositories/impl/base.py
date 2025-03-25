from typing import Dict, List, TypeVar, Any, Optional, Tuple

from doorbell_api.configs.db import Base, BaseRepo
from ..abc.base import IBaseRepository

TModel = TypeVar('TModel', bound=Base)


class BaseRepository(BaseRepo[TModel], IBaseRepository):

    async def get_by_field(self, field_name: str, value: Any) -> Optional[TModel]:
        return await super().get_by_field(field_name, value)

    async def get_or_create(self, defaults: Optional[dict] = None, **kwargs) -> Tuple[TModel, bool]:
        return await super().get_or_create(**kwargs)

    async def get_all_models(self, **data: Dict[str, any]) -> List[TModel]:
        return await super().get_all(**data)

    async def get_model_by_id(self, model_id: int) -> TModel:
        return await super().get_by_id(model_id)

    async def create_model(self, model: TModel) -> TModel:
        return await super().save(model)

    async def update_model_by_id(self, model_id: int, params: Dict[str, any]) -> TModel:
        return await super().update_by_id(model_id, params)

    async def delete_model_by_id(self, model_id: int) -> None:
        await super().delete_by_id(model_id)

    async def delete_model(self, model: TModel) -> None:
        await super().delete(model)

    async def count_hits(self, filter_by: Optional[Dict[str, Any]] = None) -> int:
        return await super().count_all(filter_by=filter_by)

    async def delete_models_by_ids(self, model_ids: List[int]) -> int:
        return await super().delete_by_ids(model_ids)

