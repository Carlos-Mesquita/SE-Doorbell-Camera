from abc import ABC, abstractmethod
from typing import Tuple, Optional, TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from ...dtos import UserCredentialsDTO


class IAuthService(ABC):

    @abstractmethod
    async def create_access_and_refresh_tokens(self, creds: "UserCredentialsDTO") -> Optional[Tuple[str, str]]:
        pass

    @abstractmethod
    async def create_access_token_from_refresh_token(self, refresh_token: str) -> Optional[str]:
        pass

    @abstractmethod
    async def revoke_refresh_token(self, refresh_token: str):
        pass

    @abstractmethod
    async def authenticate_user(self, creds: "UserCredentialsDTO") -> str:
        pass

    @staticmethod
    @abstractmethod
    async def decode_token(access_token: str, refresh: bool = False) -> Dict[str, Any]:
        pass
