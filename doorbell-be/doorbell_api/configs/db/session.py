import os
from contextvars import ContextVar, Token
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_scoped_session,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase

load_dotenv()

env = os.environ.get('ENV', 'LOCAL').upper()
connection_string = os.environ[f'DB_CONNECTION_STRING_{env}']

session_context: ContextVar[str] = ContextVar("session_context")


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)


engine = create_async_engine(connection_string, pool_recycle=3600)

async_session_factory = async_sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False,
    bind=engine
)

scoped_session = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=get_session_context,
)


class Base(DeclarativeBase):
    ...


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    try:
        yield scoped_session()
    finally:
        await scoped_session.remove()
