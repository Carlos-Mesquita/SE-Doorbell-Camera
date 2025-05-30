import bcrypt
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from uuid import UUID, uuid4
from dependency_injector.wiring import inject, Provide

from ...dtos import UserCredentialsDTO
from ...exceptions import ExpiredTokenException, UnauthorizedException
from ...helpers import TokenHelper
from ...repositories import IUserRepository
from ...services import IAuthService, ITokenService


class AuthService(IAuthService):

    @inject
    def __init__(
        self,
        token_service: ITokenService = Provide['token_service'],
        user_repo: IUserRepository = Provide['user_repo'],
        config: Dict[str, Any] = Provide['config']
    ):
        self._token_service = token_service
        self._user_repo = user_repo
        self._config = config

    async def create_access_and_refresh_tokens(self, creds: UserCredentialsDTO) -> Optional[Tuple[str, str]]:
        uid = await self.authenticate_user(creds)

        access_token = TokenHelper.encode(
            payload={
                "sub": str(uid)
            },
            key=self._config["jwt"]["access"]["key"],
            expire_period=(datetime.now() + timedelta(seconds=int(self._config["jwt"]["access"]["expires"]))),
            config=self._config
        )

        guid = uuid4()
        created_at = datetime.now()
        expires = created_at + timedelta(seconds=int(self._config["jwt"]["refresh"]["expires"]))

        await self._token_service.store_refresh_token(guid, created_at, expires)

        refresh_token = TokenHelper.encode(
            payload={
                "guid": guid.__str__(),
                "sub": str(uid)
            },
            key=self._config["jwt"]["refresh"]["key"],
            expire_period=(created_at + timedelta(seconds=int(self._config["jwt"]["refresh"]["expires"]))),
            config=self._config
        )
        return access_token, refresh_token

    async def create_access_token_from_refresh_token(self, refresh_token: str) -> Optional[str]:
        refresh_token_payload = TokenHelper.decode(token=refresh_token, config=self._config)
        guid = refresh_token_payload.get("guid")

        if not await self._token_service.is_refresh_token_valid(UUID(guid)):
            raise ExpiredTokenException

        access_token = TokenHelper.encode(
            payload={
                "sub": refresh_token_payload.get("id")
            },
            key=self._config["jwt"]["access"]["key"],
            expire_period=(datetime.now() + timedelta(seconds=int(self._config["jwt"]["access"]["expires"]))),
            config=self._config
        )
        return access_token

    @staticmethod
    def _verify_password(user_pwd, pwd):
        return bcrypt.checkpw(
            user_pwd.encode('utf-8'),
            pwd.encode('utf-8')
        )

    async def authenticate_user(self, creds: UserCredentialsDTO) -> int:
        user = await self._user_repo.get_by_email(creds.email)
        if not user or not self._verify_password(creds.password, user.password):
            raise UnauthorizedException
        return int(user.id)

    async def revoke_refresh_token(self, refresh_token: str):
        await self._token_service.revoke_refresh_token(UUID(refresh_token))

    async def decode_token(self, token: str, refresh: bool = False) -> Dict[str, Any]:
        return TokenHelper.decode(token=token, refresh=refresh, config=self._config)
