from datetime import datetime
from uuid import UUID

from ...dtos import TokenDTO
from ...configs.db import Transactional
from ...repositories import ITokenRepository
from doorbell_api.services import ITokenService


class TokenService(ITokenService):
    def __init__(self, token_repo: ITokenRepository):
        self._repository = token_repo

    @Transactional()
    async def store_refresh_token(self, guid: UUID, created_at: datetime, expires_at: datetime):
        token_dto = TokenDTO(
            guid=guid,
            created_at=created_at,
            expires_at=expires_at,
        )

        await self._repository.store_refresh_token(token_dto)
        return token_dto

    async def is_refresh_token_valid(self, guid: UUID) -> bool:
        return await self._repository.is_refresh_token_valid(guid)

    @Transactional()
    async def revoke_refresh_token(self, guid: UUID):
        await self._repository.revoke_refresh_token(guid)

    # API Token management is done via cmd
    async def validate_api_token(self, guid: UUID) -> bool:
        return await self._repository.is_api_token_valid(guid)
