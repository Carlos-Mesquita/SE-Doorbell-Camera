from typing import Type, TypeVar, Optional, Dict, Generic, List, Union, Any
from inspect import isclass

from pydantic import BaseModel
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
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
            exclude_orm_keys: Optional[set[str]] = None,
            relationship_mappers: Optional[Dict[str, 'Mapper']] = None
    ):
        self.orm_model = orm_model
        self.dto_model = dto_model
        self.field_mapping = field_mapping or {}
        self.exclude_dto_keys = exclude_dto_keys or set()
        self.exclude_orm_keys = exclude_orm_keys or set()
        self.relationship_mappers = relationship_mappers or {}

        # Auto-discover relationships if not provided
        self._discover_relationships()

    def _discover_relationships(self):
        """Auto-discover ORM relationships for this model"""
        mapper = sqlalchemy_inspect(self.orm_model)
        self.relationships = {}

        for prop in mapper.attrs:
            if isinstance(prop, RelationshipProperty):
                self.relationships[prop.key] = {
                    'is_collection': prop.collection_class is not None,
                    'related_model': prop.mapper.class_
                }

    def add_relationship_mapper(self, relationship_name: str, mapper: 'Mapper'):
        """Add a mapper for a specific relationship"""
        self.relationship_mappers[relationship_name] = mapper

    def to_orm(self, dto: TDTO, existing_model: Optional[TORM] = None) -> TORM:
        if existing_model:
            return self._update_existing_model(dto, existing_model)
        else:
            return self._create_new_model(dto)

    def to_dto(self, orm_model: TORM, exclusions: Optional[set[str]] = None) -> TDTO:
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

    def _convert_orm_to_dto(self, orm_model: TORM, exclusions: Optional[set[str]] = None) -> TDTO:
        if orm_model is None:
            return None

        exclusions = exclusions or set()
        reversed_field_mapping = {v: k for k, v in self.field_mapping.items()}
        orm_dict = {}

        for orm_field in dir(orm_model):
            if orm_field.startswith('_'):
                continue

            dto_field = reversed_field_mapping.get(orm_field, orm_field)
            if dto_field in exclusions or orm_field in self.exclude_orm_keys:
                continue

            try:
                value = getattr(orm_model, orm_field, None)

                if callable(value):
                    continue

                if orm_field in self.relationships:
                    processed_value = self._process_relationship(orm_field, value)
                    if processed_value is not None:
                        orm_dict[dto_field] = processed_value

                elif not orm_field in self.relationships:
                    if self._field_exists_in_dto(dto_field):
                        orm_dict[dto_field] = value

            except Exception as e:
                continue

        for orm_field in self.field_mapping.values():
            if orm_field in self.exclude_orm_keys:
                continue

            dto_field = reversed_field_mapping.get(orm_field, orm_field)
            if dto_field in exclusions:
                continue

            try:
                value = getattr(orm_model, orm_field, None)

                if orm_field in self.relationships:
                    processed_value = self._process_relationship(orm_field, value)
                    if processed_value is not None:
                        orm_dict[dto_field] = processed_value
                else:
                    orm_dict[dto_field] = value

            except Exception:
                continue

        return self.dto_model(**orm_dict)

    def _process_relationship(self, relationship_name: str, value: Any) -> Any:
        """Process a relationship value, converting ORM objects to DTOs"""
        if value is None:
            return None

        relationship_info = self.relationships.get(relationship_name, {})
        is_collection = relationship_info.get('is_collection', False)

        # Check if we have a dedicated mapper for this relationship
        if relationship_name in self.relationship_mappers:
            mapper = self.relationship_mappers[relationship_name]

            if is_collection:
                return [mapper.to_dto(item) for item in value if item is not None]
            else:
                return mapper.to_dto(value)

        if is_collection:
            return [self._orm_to_dict(item) for item in value if item is not None]
        else:
            return self._orm_to_dict(value)

    def _orm_to_dict(self, orm_obj: Any) -> Dict[str, Any]:
        """Convert ORM object to dictionary for simple cases"""
        if orm_obj is None:
            return None

        result = {}

        mapper = sqlalchemy_inspect(orm_obj.__class__)
        for column in mapper.columns:
            try:
                value = getattr(orm_obj, column.name, None)
                result[column.name] = value
            except Exception:
                continue

        return result

    def _field_exists_in_dto(self, field_name: str) -> bool:
        try:
            return field_name in self.dto_model.model_fields
        except Exception:
            return False