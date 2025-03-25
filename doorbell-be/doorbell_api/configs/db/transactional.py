from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession
from .session import scoped_session


class Transactional:
    def __call__(self, func):
        @wraps(func)
        async def _transactional(*args, **kwargs):
            session: AsyncSession = scoped_session()
            try:
                result = await func(*args, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise e

        return _transactional