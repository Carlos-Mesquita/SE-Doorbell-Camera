from abc import ABC, abstractmethod
from typing import Dict, List, TypeVar, Generic, Optional, Tuple, Any
from ...configs.db import Base

TModel = TypeVar('TModel', bound=Base)


class IBaseRepository(ABC, Generic[TModel]):

    @abstractmethod
    async def get_or_create(self, defaults: Optional[dict] = None, **kwargs) -> Tuple[TModel, bool]:
        pass

    @abstractmethod
    async def get_all_models(self, filter_by: Optional[Dict[str, Any]] = None, **pagination: Dict[str, any]) -> List[
        TModel]:
        pass

    @abstractmethod
    async def get_model_by_id(self, model_id: int) -> TModel:
        pass

    @abstractmethod
    async def create_model(self, model: TModel) -> TModel:
        pass

    @abstractmethod
    async def update_model_by_id(self, model_id: int, params: Dict[str, any]) -> TModel:
        pass

    @abstractmethod
    async def delete_model_by_id(self, model_id: int) -> None:
        pass

    @abstractmethod
    async def delete_models_by_ids(self,model_ids: List[int]) -> int:
        pass

    @abstractmethod
    async def delete_model(self, model: TModel) -> None:
        pass

    @abstractmethod
    async def count_hits(self, filter_by: Optional[Dict[str, Any]] = None) -> int:
        pass
