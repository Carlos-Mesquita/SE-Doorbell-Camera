from fastapi import APIRouter, Depends
from dependency_injector.wiring import Provide, inject

from doorbell_api.middlewares import OAuth2Authorized
from doorbell_api.services import IWebRTCSignalingService

webrtc_router = APIRouter()
controller_name = "signaling_service"


@webrtc_router.get(
    "/rooms",
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_active_rooms(
    signaling_service: IWebRTCSignalingService = Depends(Provide[controller_name])
):
    return signaling_service.get_active_rooms()


@webrtc_router.get(
    "/rooms/{room_id}/clients",
    dependencies=[Depends(OAuth2Authorized)]
)
@inject
async def get_room_clients(
    room_id: str,
    signaling_service: IWebRTCSignalingService = Depends(Provide[controller_name])
):
   return signaling_service.get_room_clients(room_id)
