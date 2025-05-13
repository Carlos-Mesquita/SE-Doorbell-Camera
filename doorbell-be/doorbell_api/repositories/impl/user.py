from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from doorbell_api.models.user import User
from doorbell_api.repositories import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def get_by_email(self, email: str) -> Optional[User]:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalars().first()
