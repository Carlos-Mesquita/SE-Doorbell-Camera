from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from doorbell_api.dtos import CaptureDTO
from doorbell_api.controllers import ICaptureController
from doorbell_api.dtos.hits import HitsDTO
from doorbell_api.middlewares import OAuth2Authorized

capture_router = APIRouter()

controller_name = "capture_controller"


@capture_router.get(
    "/",
    response_model=List[CaptureDTO],
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_all_captures(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1),
    sort_by: Optional[str] = Query(None),
    sort_order: Optional[str] = Query(None),
    controller: ICaptureController = Depends(Provide[controller_name])
):
    pagination = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_order": sort_order
    }
    return await controller.get_all(**pagination)


@capture_router.get(
    "/count",
    response_model=HitsDTO,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_hits(
    controller: ICaptureController = Depends(Provide[controller_name])
):
    return await controller.count_all()


@capture_router.delete(
    "/",
    status_code=200,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def delete_capture(
    ids: List[int],
    controller: ICaptureController = Depends(Provide[controller_name])
):
    await controller.delete_by_ids(ids)
