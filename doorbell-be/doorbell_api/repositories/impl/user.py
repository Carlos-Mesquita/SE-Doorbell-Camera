from typing import Optional

from sqlalchemy import select

from doorbell_api.configs.db import BaseRepo
from doorbell_api.models.user import User
from doorbell_api.repositories import IUserRepository


class UserRepository(BaseRepo[User], IUserRepository):
    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()
