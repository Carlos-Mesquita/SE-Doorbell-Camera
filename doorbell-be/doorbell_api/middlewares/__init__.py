from typing import List

from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.authentication import AuthenticationMiddleware

from .auth import AuthBackend, ApiKeyAuthorized, OAuth2Authorized
from .context import SessionContextMiddleware

def setup_middlewares() -> List[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware, # type: ignore
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(
            AuthenticationMiddleware, # type: ignore
            backend=AuthBackend()
        ),
        Middleware(SessionContextMiddleware) # type: ignore
    ]
    return middleware


__all__ = [
    "setup_middlewares",
    "ApiKeyAuthorized",
    "OAuth2Authorized"
]
