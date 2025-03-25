from abc import ABC, abstractmethod
from typing import List, Type, Optional

from fastapi import Request
from fastapi.openapi.models import APIKey, APIKeyIn, HTTPBearer
from fastapi.security.base import SecurityBase

from doorbell_api.exceptions import CustomAPIException, UnauthorizedException


# If more granular access is required use this
class BaseIsAuthorized(ABC):
    exception = CustomAPIException

    @abstractmethod
    async def is_authorized(self, request: Request) -> bool:
        pass

# Example of a BaseIsAuthorized implementation
"""
class IsAdmin(BaseIsAuthorized):
    exception = IsNotAdmin

    async def is_authorized(self, request: Request) -> bool:
        return 'admin' in request.auth.scopes
        
OAuth2Authorized([IsAdmin])
"""

class Authorized(SecurityBase):
    def __init__(self, scheme: str, rules: Optional[List[Type[BaseIsAuthorized]]] = None):
        if scheme not in ['ApiKey', 'OAuth2']:
            raise ValueError('Only accepted schemes are ApiKey or OAuth2')

        self.model = (
            APIKey(**{'in': APIKeyIn.header}, name='Authorization')
            if scheme == 'ApiKey'
            else HTTPBearer()
        )
        self.scheme_name = scheme
        self._rules = rules

    async def __call__(self, request: Request):
        if self.scheme_name == 'ApiKey':
            if (
                not request.user.is_authenticated
                or 'apikey' not in request.auth.scopes
            ):
                raise UnauthorizedException

        if self.scheme_name == 'OAuth2':
            if (
                not request.user.is_authenticated
                or 'bearer' not in request.auth.scopes
            ):
                raise UnauthorizedException

        if self._rules is not None:
            for rule in self._rules:
                cls = rule()
                if not await cls.is_authorized(request):
                    raise cls.exception


class ApiKeyAuthorized(Authorized):
    def __init__(self, rules: Optional[List[Type[BaseIsAuthorized]]] = None):
        super().__init__('ApiKey', rules)

class OAuth2Authorized(Authorized):
    def __init__(self, rules: Optional[List[Type[BaseIsAuthorized]]] = None):
        super().__init__('OAuth2', rules)
