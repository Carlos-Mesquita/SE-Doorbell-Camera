from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Path
from doorbell_api.dtos.settings import SettingsDTO
from doorbell_api.controllers import ISettingsController
from doorbell_api.middlewares import OAuth2Authorized

settings_router = APIRouter()

controller_name = "settings_controller"


@settings_router.get(
    "/",
    response_model=SettingsDTO,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_settings(
    controller: ISettingsController = Depends(Provide[controller_name])
):
    # Only one row will be used
    return await controller.get_by_id(1)


@settings_router.put(
    "/",
    response_model=SettingsDTO,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def update_settings(
    dto: SettingsDTO,
    controller: ISettingsController = Depends(Provide[controller_name])
):
    # Only one row will be used
    return await controller.update_by_id(1, dto)
