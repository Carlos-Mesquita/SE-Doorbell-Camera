from uuid import uuid4

from starlette.middleware.base import (BaseHTTPMiddleware,
                                       RequestResponseEndpoint)
from starlette.requests import Request
from ..configs.db.context import orm_session_context


class ContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        uuid = str(uuid4())

        context_token = orm_session_context.set(uuid)
        try:
            response = await call_next(request)
        finally:
            orm_session_context.reset(context_token)
        return response
