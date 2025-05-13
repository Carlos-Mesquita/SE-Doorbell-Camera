import bcrypt
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any
from uuid import UUID, uuid4

from doorbell_api.dtos import UserCredentialsDTO
from doorbell_api.exceptions import ExpiredTokenException, UnauthorizedException
from doorbell_api.helpers import TokenHelper
from doorbell_api.repositories import IUserRepository
from doorbell_api.services import IAuthService, ITokenService


class AuthService(IAuthService):

    def __init__(
        self, token_service: ITokenService, user_repo: IUserRepository, config: Dict[str, Any]
    ):
        self._token_service = token_service
        self._user_repo = user_repo
        self._config = config

    async def create_access_and_refresh_tokens(self, creds: UserCredentialsDTO) -> Optional[Tuple[str, str]]:
        uid = await self.authenticate_user(creds)

        access_token = TokenHelper.encode(
            payload={
                "id": uid,
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
                "id": uid
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
                "id": refresh_token_payload.get("id")
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

    async def authenticate_user(self, creds: UserCredentialsDTO) -> str:
        user = await self._user_repo.get_by_email(creds.email)
        if not user or not self._verify_password(creds.password, user.password):
            raise UnauthorizedException
        return str(user.id)

    async def revoke_refresh_token(self, refresh_token: str):
        await self._token_service.revoke_refresh_token(UUID(refresh_token))

    async def decode_token(self, token: str, refresh: bool = False) -> Optional[str]:
        return TokenHelper.decode(token=token, refresh=refresh, config=self._config)["id"]
