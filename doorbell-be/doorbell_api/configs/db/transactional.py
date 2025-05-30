from functools import wraps
from typing import Any, Callable, TypeVar, cast

from sqlalchemy.ext.asyncio import AsyncSession

from .context import get_db_instance

R = TypeVar('R')
F = TypeVar('F', bound=Callable[..., Any])


def transactional(func: Callable[..., Any]) -> Callable[..., Any]:
    db = get_db_instance()

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        session = db.scoped_session()
        session = cast(AsyncSession, session)

        try:
            result = await func(*args, **kwargs)
            await session.commit()
            return result
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await db.scoped_session.remove()

    return async_wrapper

