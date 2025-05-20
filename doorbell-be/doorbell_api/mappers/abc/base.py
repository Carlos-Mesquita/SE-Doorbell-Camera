from abc import ABC, abstractmethod
from typing import TypeVar, Optional, Generic, Dict, List
from pydantic import BaseModel
from ...configs.db import Base

TDTO = TypeVar('TDTO', bound=BaseModel)
TORM = TypeVar('TORM', bound=Base)


class IMapper(ABC, Generic[TDTO, TORM]):

    @abstractmethod
    def to_orm(self, dto: TDTO, existing_model: Optional[TORM] = None) -> TORM:
        pass

    @abstractmethod
    def to_dto(self, orm_model: TORM, exclusions: Optional[List[str]] = None) -> TDTO:
        pass

    @abstractmethod
    def dto_kwargs(self, dto: TDTO) -> Dict[str, any]:
        pass

    @abstractmethod
    def _update_existing_model(self, dto: TDTO, existing_model: TORM) -> TORM:
        pass

    @abstractmethod
    def _create_new_model(self, dto: TDTO) -> TORM:
        pass

    @abstractmethod
    def _convert_orm_to_dto(self, orm_model: TORM) -> TDTO:
        pass
