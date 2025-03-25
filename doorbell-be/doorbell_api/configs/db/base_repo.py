from typing import TypeVar, Type, Generic, List, Optional, ClassVar, Tuple, cast, Dict, Any, Sequence

from pydantic import BaseModel
from sqlalchemy.exc import NoResultFound, IntegrityError
from sqlalchemy import select, update, delete, desc, asc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import BinaryExpression, and_

from .session import Base

TModel = TypeVar('TModel', bound=Base)


class BaseRepo(Generic[TModel]):
    def __init__(self, model: Type[TModel], db_session: AsyncSession):
        self._model = model
        self.session = db_session

    def _build_filter_conditions(self, filter_by: Dict[str, Any]) -> Sequence[BinaryExpression]:
        filter_conditions = []

        for field, value in filter_by.items():
            column = getattr(self._model, field, None)
            if column is None:
                raise ValueError(f"Field {field} does not exist in model {self._model.__name__}")

            if isinstance(value, list):
                filter_conditions.append(column.in_(value))
            elif isinstance(value, dict):
                for op, op_value in value.items():
                    if op == 'gt':
                        filter_conditions.append(column > op_value)
                    elif op == 'lt':
                        filter_conditions.append(column < op_value)
                    elif op == 'ge':
                        filter_conditions.append(column >= op_value)
                    elif op == 'le':
                        filter_conditions.append(column <= op_value)
                    elif op == 'ne':
                        filter_conditions.append(column != op_value)
                    elif op == 'like':
                        filter_conditions.append(column.like(f"%{op_value}%"))
                    else:
                        raise ValueError(f"Unknown operator {op}")
            else:
                filter_conditions.append(column == value)

        return filter_conditions

    async def get_all(
            self,
            page: int = 0,
            page_size: int = 100,
            sort_by: Optional[str] = None,
            sort_order: str = 'asc',
            filter_by: Optional[Dict[str, Any]] = None
    ) -> List[TModel]:
        skip = (page - 1) * page_size
        query = select(self._model)

        if filter_by:
            filter_conditions = self._build_filter_conditions(filter_by)
            if filter_conditions:
                query = query.where(and_(*filter_conditions))

        if sort_by:
            column = getattr(self._model, sort_by, None)
            if column is None:
                raise ValueError(f"Field {sort_by} does not exist in model {self._model.__name__}")

            if sort_order == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(asc(column))

        query = query.offset(skip).limit(page_size)
        result = await self.session.execute(query)
        scalar_result = result.scalars().all()
        return cast(List[TModel], list(scalar_result))

    async def count_all(
            self,
            filter_by: Optional[Dict[str, Any]] = None
    ) -> int:
        count_query = select(func.count()).select_from(self._model)

        if filter_by:
            filter_conditions = self._build_filter_conditions(filter_by)
            if filter_conditions:
                count_query = count_query.where(and_(*filter_conditions))

        result = await self.session.execute(count_query)
        total_count = result.scalar_one()

        return total_count


    async def get_by_id(self, model_id: int) -> TModel:
        result = await self.session.get(self._model, model_id)

        if not result:
            raise NoResultFound(f"No {self._model.__name__} found with id {model_id}")
        return cast(TModel, result)

    async def update_by_id(
            self,
            model_id: int,
            params: dict,
    ) -> TModel:
        id_column = getattr(self._model, "id")
        condition = cast(BinaryExpression, id_column == model_id)

        query = (
            update(self._model)
            .where(condition)
            .values(**params)
        )
        result = await self.session.execute(query)

        if result.rowcount == 0:
            raise NoResultFound(f"No {self._model.__name__} found with id {model_id}")

        return await self.get_by_id(model_id)

    async def delete(self, model: TModel) -> None:
        await self.session.delete(model)

    async def get_by_field(self, field_name: str, value: Any) -> Optional[TModel]:
        column = getattr(self._model, field_name)
        condition = cast(BinaryExpression, column == value)

        query = select(self._model).where(condition)
        result = await self.session.execute(query)
        return cast(Optional[TModel], result.scalars().first())

    async def get_or_create(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[TModel, bool]:
        query = select(self._model)
        for field, value in kwargs.items():
            column = getattr(self._model, field)
            condition = cast(BinaryExpression, column == value)
            query = query.where(condition)

        result = await self.session.execute(query)
        instance = result.scalars().first()

        if instance:
            typed_instance = cast(TModel, instance)
            return typed_instance, False

        create_data = kwargs.copy()
        if defaults:
            create_data.update(defaults)

        instance = self._model(**create_data)
        self.session.add(instance)
        await self.session.flush()
        typed_instance = cast(TModel, instance)
        return typed_instance, True

    async def delete_by_id(
            self,
            model_id: int,
    ) -> None:
        id_column = getattr(self._model, "id")
        condition = cast(BinaryExpression, id_column == model_id)

        query = (
            delete(self._model)
            .where(condition)
        )
        result = await self.session.execute(query)
        if result.rowcount == 0:
            raise NoResultFound(f"No {self._model.__name__} found with id {model_id}")

    async def delete_by_ids(
            self,
            model_ids: List[int],
    ) -> int:
        if not model_ids:
            return 0

        id_column = getattr(self._model, "id")

        query = (
            delete(self._model)
            .where(id_column.in_(model_ids))
        )

        result = await self.session.execute(query)
        deleted_count = result.rowcount()

        return deleted_count

    async def save(self, model: TModel) -> TModel:
        self.session.add(model)
        await self.session.flush()
        return model
