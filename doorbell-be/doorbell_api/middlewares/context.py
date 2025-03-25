from logging import getLogger
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from doorbell_api.configs.db import set_session_context, reset_session_context, scoped_session
from starlette.requests import Request

logger = getLogger(__name__)

class SessionContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        token = set_session_context(request_id)

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Request {request_id} failed: {str(e)}")
            raise
        finally:
            try:
                await scoped_session.remove()
                reset_session_context(token)
            except Exception as e:
                logger.error(f"Failed to cleanup session {request_id}: {str(e)}")
                raise
