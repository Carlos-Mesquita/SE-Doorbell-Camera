from abc import ABC, abstractmethod
from ...dtos import UserCredentialsDTO


class IAuthController(ABC):

    @abstractmethod
    async def generate_tokens(self, creds: UserCredentialsDTO):
        pass

    @abstractmethod
    async def generate_access_token(self, refresh_token: str):
        pass

    @abstractmethod
    async def revoke_refresh_token(self, refresh_token: str):
        pass
