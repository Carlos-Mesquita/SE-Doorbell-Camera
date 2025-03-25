from typing import Type, TypeVar, Optional, Dict, Generic

from pydantic import BaseModel
from doorbell_api.configs.db import Base
from doorbell_api.mappers import IMapper

TDTO = TypeVar('TDTO', bound=BaseModel)
TORM = TypeVar('TORM', bound=Base)


class Mapper(IMapper, Generic[TDTO, TORM]):
    def __init__(
            self,
            orm_model: Type[TORM],
            dto_model: Type[TDTO],
            field_mapping: Optional[Dict[str, str]] = None,
            exclude_dto_keys: Optional[set[str]] = None,
            exclude_orm_keys: Optional[set[str]] = None
    ):
        self.orm_model = orm_model
        self.dto_model = dto_model
        self.field_mapping = field_mapping or {}
        self.exclude_dto_keys = exclude_dto_keys or set()
        self.exclude_orm_keys = exclude_orm_keys or set()

    def to_orm(self, dto: TDTO, existing_model: Optional[TORM] = None) -> TORM:
        if existing_model:
            return self._update_existing_model(dto, existing_model)
        else:
            return self._create_new_model(dto)

    def to_dto(self, orm_model: TORM, exclusions = None) -> TDTO:
        return self._convert_orm_to_dto(orm_model, exclusions)

    def dto_kwargs(self, dto: TDTO) -> Dict[str, any]:
        kwargs = {
            self.field_mapping.get(field, field): value
            for field, value in dto.model_dump(exclude=set(self.exclude_dto_keys)).items()
            if field not in self.exclude_orm_keys
        }
        return kwargs

    def _update_existing_model(self, dto: TDTO, existing_model: TORM) -> TORM:
        for field, value in dto.model_dump(exclude=set(self.exclude_dto_keys)).items():
            orm_field = self.field_mapping.get(field, field)
            if orm_field not in self.exclude_orm_keys and hasattr(existing_model, orm_field):
                setattr(existing_model, orm_field, value)
        return existing_model

    def _create_new_model(self, dto: TDTO) -> TORM:
        kwargs = {
            self.field_mapping.get(field, field): value
            for field, value in dto.model_dump(exclude=set(self.exclude_dto_keys)).items()
            if field not in self.exclude_orm_keys
        }
        return self.orm_model(**kwargs)

    def _convert_orm_to_dto(self, orm_model: TORM, exclusions = None) -> TDTO:
        reversed_field_mapping = {v: k for k, v in self.field_mapping.items()}
        orm_dict = {
            reversed_field_mapping.get(orm_field, orm_field): getattr(orm_model, orm_field, None)
            for orm_field in self.field_mapping.values()
            if orm_field not in self.exclude_orm_keys and (exclusions is None or reversed_field_mapping.get(orm_field, orm_field) not in exclusions)
        }
        res = self.dto_model(**orm_dict)
        return res
