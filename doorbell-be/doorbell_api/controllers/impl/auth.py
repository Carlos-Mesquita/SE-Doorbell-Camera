from fastapi.responses import JSONResponse, Response

from ...controllers import IAuthController
from ...dtos import UserCredentialsDTO
from ...services import IAuthService


class AuthController(IAuthController):

    def __init__(self, service: IAuthService):
        self._service = service

    async def generate_tokens(self, creds: UserCredentialsDTO):
        access_token, refresh_token = await self._service.create_access_and_refresh_tokens(creds)
        response = JSONResponse(status_code=200, content={"access_token": access_token})
        response.set_cookie(key=refresh_token, value=refresh_token, httponly=True)
        return response

    async def generate_access_token(self, refresh_token: str):
        token = await self._service.create_access_token_from_refresh_token(refresh_token)
        return JSONResponse(
            status_code=200,
            content={"access_token": token}
        )

    async def revoke_refresh_token(self, refresh_token: str):
        await self._service.revoke_refresh_token(refresh_token)
        response = Response(status_code=200)
        return response
