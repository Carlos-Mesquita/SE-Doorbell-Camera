from abc import ABC, abstractmethod
from typing import TypeVar, List, Dict, Generic, Any, Optional
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel


TDTO = TypeVar('TDTO', bound=BaseModel)
TModel = TypeVar('TModel', bound=DeclarativeBase)


class IBaseService(ABC, Generic[TDTO, TModel]):

    @abstractmethod
    async def get_all(self, **data: Dict[str, Any]) -> List[TDTO]:
        pass

    @abstractmethod
    async def get_by_id(self, model_id: int) -> TDTO:
        pass

    @abstractmethod
    async def create(self, dto: TDTO) -> TDTO:
        pass

    @abstractmethod
    async def update_by_id(self, model_id: int, dto: TDTO) -> TDTO:
        pass

    @abstractmethod
    async def delete_by_id(self, model_id: int) -> None:
        pass

    @abstractmethod
    async def delete_by_ids(self, model_ids: List[int]) -> int:
        pass

    @abstractmethod
    async def count_all(self, filter_by: Optional[Dict[str, Any]] = None) -> int:
        pass
