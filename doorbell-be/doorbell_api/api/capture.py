from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, Path
from typing import List, Optional
from ..dtos import CaptureDTO
from ..controllers import ICaptureController
from ..middlewares import OAuth2Authorized
from pydantic import BaseModel

capture_router = APIRouter()

controller_name = "capture_controller"

class CaptureVideoRequest(BaseModel):
    capture_paths: List[str]

@capture_router.post(
"",
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def generate_stop_motion_video(
    request: CaptureVideoRequest,
    controller: ICaptureController = Depends(Provide[controller_name])
):
    return await controller.generate_cap_video(request.capture_paths)


@capture_router.get(
    "",
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

@capture_router.delete(
    "{capture_id}",
    status_code=204,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def delete_single_capture(
    capture_id: int = Path(..., ge=1),
    controller: ICaptureController = Depends(Provide[controller_name])
):
    await controller.delete_by_id(capture_id)


@capture_router.delete(
    "",
    status_code=200,
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def delete_capture(
    ids: List[int],
    controller: ICaptureController = Depends(Provide[controller_name])
):
    await controller.delete_by_ids(ids)
