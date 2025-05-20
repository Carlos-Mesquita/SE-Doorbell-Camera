import jwt

from typing import Tuple
from fastapi import Depends
from dependency_injector.wiring import Provide

from starlette.authentication import AuthenticationBackend, AuthCredentials
from starlette.requests import HTTPConnection

from .user import User

config = Provide["config"]


class AuthBackend(AuthenticationBackend):

    async def authenticate(
        self, conn: HTTPConnection, api_key_repo=Depends(Provide['api_key_repository'])
    ) -> Tuple[AuthCredentials, User]:
        user = User()
        unauthenticated = AuthCredentials([])

        authorization: str = conn.headers.get('Authorization')

        if not authorization:
            return unauthenticated, user

        try:
            scheme, credentials = authorization.split(' ')
            if scheme.lower() not in ['bearer', 'apikey']:
                return unauthenticated, user
        except ValueError:
            return unauthenticated, user

        if scheme.lower() == 'bearer':
            try:
                payload = jwt.decode(
                    credentials,
                    config['jwt']['access']['key'],
                    algorithms=[config['jwt']['algorithm']],
                )

                user_id = payload.get('id')
                creds = AuthCredentials(['bearer'])
                user.identity = user_id

            except jwt.exceptions.PyJWTError:
                return unauthenticated, user
        else:
            key = await api_key_repo.get(credentials)

            if not key:
                return unauthenticated, user
            else:
                user_id = 'api'
                creds = AuthCredentials(['apikey'])

        user.is_authenticated = True
        user.identity = user_id

        return creds, user
