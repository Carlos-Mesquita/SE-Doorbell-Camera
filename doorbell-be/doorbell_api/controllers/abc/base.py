from abc import ABC, abstractmethod
from typing import TypeVar, List, Dict, Generic, Any, Optional
from pydantic import BaseModel


TDTO = TypeVar('TDTO', bound=BaseModel)


class IBaseController(ABC, Generic[TDTO]):

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
