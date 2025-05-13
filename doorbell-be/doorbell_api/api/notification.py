from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from doorbell_api.dtos import NotificationDTO
from doorbell_api.controllers import INotificationController
from doorbell_api.dtos import HitsDTO
from doorbell_api.middlewares import OAuth2Authorized

notification_router = APIRouter()

controller_name = "notification_controller"


@notification_router.get(
    "",
    response_model=List[NotificationDTO],
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_all_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    controller: INotificationController = Depends(Provide[controller_name])
):
    pagination = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    return await controller.get_all(**pagination)


@notification_router.get(
    "/count",
    response_model=HitsDTO,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_hits(
    controller: INotificationController = Depends(Provide[controller_name])
):
    return await controller.count_all()

@notification_router.delete(
    "/{model_id}",
    status_code=204,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def delete_notification(
    model_id: int = Path(..., ge=1),
    controller: INotificationController = Depends(Provide[controller_name])
):
    await controller.delete_by_id(model_id)


@notification_router.delete(
    "",
    status_code=204,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def delete_notifications(
    ids: List[int],
    controller: INotificationController = Depends(Provide[controller_name])
):
    await controller.delete_by_ids(ids)
