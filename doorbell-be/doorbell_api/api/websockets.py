import logging

from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Query
from starlette.websockets import WebSocket
from ..controllers import IWebSocketController

logger = logging.getLogger(__name__)

ws_router = APIRouter()
controller = 'ws_controller'

@ws_router.websocket(
    "/messages"
)
@inject
async def device_messages(
    websocket: WebSocket,
    token: str = Query(),
    ws_controller: IWebSocketController = Depends(Provide[controller])
):
    await ws_controller.handle_camera_events(websocket, token)


@ws_router.websocket(
    "/webrtc"
)
@inject
async def webrtc_signaling(
    websocket: WebSocket,
    token: str = Query(),
    ws_controller: IWebSocketController = Depends(Provide[controller])
):
    await ws_controller.handle_signaling(websocket, token)
