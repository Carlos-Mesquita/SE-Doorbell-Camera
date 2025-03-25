from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Cookie

from doorbell_api.controllers import IAuthController
from doorbell_api.dtos import UserCredentialsDTO

controller = "auth_controller"
auth_router = APIRouter()


@auth_router.post(
    ""
)
@inject
async def login(
    creds: UserCredentialsDTO,
    auth_controller: IAuthController = Depends(Provide[controller])
):
    return await auth_controller.generate_tokens(creds)


@auth_router.get(
    "/refresh"
)
@inject
async def renew(
        refresh_token: str = Cookie(),
        auth_controller: IAuthController = Depends(Provide[controller])
):
    return await auth_controller.generate_access_token(refresh_token)


@auth_router.delete(
    "/logout"
)
@inject
async def revoke_refresh_token(
        refresh_token: str = Cookie(),
        auth_controller: IAuthController = Depends(Provide[controller])
):
    return await auth_controller.generate_access_token(refresh_token)
