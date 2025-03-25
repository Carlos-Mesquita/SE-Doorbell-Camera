from abc import ABC, abstractmethod
from typing import Optional

from doorbell_api.models import User


class IUserRepository(ABC):

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        pass
