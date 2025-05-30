from contextvars import ContextVar
from typing import Optional
from .db import DB


orm_session_context: ContextVar[str] = ContextVar("orm_session_context")
db_context: ContextVar[Optional[DB]] = ContextVar('db_instance', default=None)


def get_orm_session_context() -> str:
    return orm_session_context.get()


def set_db(db_instance) -> None:
    db_context.set(db_instance)


def get_db_instance():
    db = db_context.get()
    if db is None:
        raise RuntimeError("Database not configured. Use set_db() first.")
    return db
