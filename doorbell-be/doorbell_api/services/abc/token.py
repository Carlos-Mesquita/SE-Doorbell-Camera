from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class ITokenService(ABC):

    @abstractmethod
    async def store_refresh_token(self, guid: UUID, created_at: datetime, expires_at: datetime):
        pass

    @abstractmethod
    async def is_refresh_token_valid(self, guid: UUID) -> bool:
        pass

    @abstractmethod
    async def revoke_refresh_token(self, guid: UUID):
        pass

    @abstractmethod
    async def validate_api_token(self, guid: UUID) -> bool:
        pass