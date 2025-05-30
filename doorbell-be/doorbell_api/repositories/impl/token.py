from datetime import datetime
from uuid import UUID

from ...configs.db import BaseRepo, DB
from ...dtos import TokenDTO
from ...models import Token
from ...repositories import ITokenRepository

from typing import cast, Dict, Any

from sqlalchemy import select, delete
from sqlalchemy.sql.elements import BinaryExpression
from dependency_injector.wiring import Provide, inject


class TokenRepository(BaseRepo[Token],ITokenRepository):

    @inject
    def __init__(self, config: Dict[str, Any] = Provide['config']):
        super().__init__(Token)
        self._config = config


    async def store_refresh_token(self, refresh_token_dto: TokenDTO) -> None:
        token = Token(
            guid=refresh_token_dto.guid,
            created_at=refresh_token_dto.created_at,
            expires_at=refresh_token_dto.expires_at
        )
        self.session.add(token)
        await self.session.flush()


    async def revoke_refresh_token(self, guid: UUID) -> None:
        guid_column = getattr(Token, "guid")
        guid_condition = cast(BinaryExpression, guid_column == guid)

        delete_query = delete(Token).where(guid_condition)
        await self.session.execute(delete_query)


    async def is_refresh_token_valid(self, guid: UUID) -> bool:
        guid_column = getattr(Token, "guid")
        guid_condition = cast(BinaryExpression, guid_column == guid)

        query = select(Token).where(guid_condition)
        result = await self.session.execute(query)
        token = result.scalars().first()

        if not token:
            return False

        # Must have an expiration date to be a refresh token
        if token.expires_at is None:
            return False

        refresh_token_expiry = self._config['jwt']['refresh']['expires']

        now = datetime.now()
        token_age = now - token.created_at

        if token_age > refresh_token_expiry:
            await self.revoke_refresh_token(guid)
            return False

        return True


    async def is_api_token_valid(self, guid: UUID) -> bool:
        token_column = getattr(Token, "guid")
        expires_column = getattr(Token, "expires_at")

        token_condition = cast(BinaryExpression, token_column == guid)
        api_token_condition = cast(BinaryExpression, expires_column is None)

        query = select(Token).where(token_condition, api_token_condition)
        result = await self.session.execute(query)
        token = result.scalars().first()
        return token is not None
