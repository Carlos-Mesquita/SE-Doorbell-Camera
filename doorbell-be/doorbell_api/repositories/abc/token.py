from abc import ABC, abstractmethod
from uuid import UUID

from doorbell_api.dtos import TokenDTO


class ITokenRepository(ABC):

    @abstractmethod
    async def store_refresh_token(self, refresh_token_dto: TokenDTO) -> None:
        pass

    @abstractmethod
    async def revoke_refresh_token(self, guid: UUID) -> None:
        pass

    @abstractmethod
    async def is_refresh_token_valid(self, guid: UUID) -> bool:
        pass

    @abstractmethod
    async def is_api_token_valid(self, guid: UUID) -> bool:
        pass
