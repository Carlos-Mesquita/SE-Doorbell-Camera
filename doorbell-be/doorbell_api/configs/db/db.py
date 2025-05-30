import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (AsyncSession, async_scoped_session,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    ...


class DB:
    def __init__(
        self,
        *,
        engine_kwargs = None,
        session_kwargs = None
    ):
        """
        Init the database connection.

        Args:
            engine_kwargs: Engine options kwargs
            session_kwargs: Session options kwargs
        """
        if session_kwargs is None:
            session_kwargs = {}
        if engine_kwargs is None:
            engine_kwargs = {}

        env = os.getenv("ENV")
        connection_string = os.getenv(f"{env}_DB_CONNECTION_STRING")

        if not env:
            raise RuntimeError("ENV environment variable is not set!")

        if not connection_string:
            raise RuntimeError(f"{env}_DB_CONNECTION_STRING environment variable is not set!")
        
        engine = create_async_engine(connection_string, **engine_kwargs)
        self.session_factory = async_sessionmaker(
            class_=AsyncSession,
            bind=engine,
            autocommit=False,
            autoflush=True,
            expire_on_commit=False,
            **session_kwargs
        )
        from .context import get_orm_session_context
        self.scoped_session = async_scoped_session(
            self.session_factory,
            scopefunc=get_orm_session_context
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        If you extend BaseORMRepository and use @transactional properly
        you probably won't need this but still here if needed.

        Example:
            async with db.get_session() as session:
                result = await session...
        
        Returns:
            An async generator yielding the session.
        """
        session = self.session_factory()

        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
