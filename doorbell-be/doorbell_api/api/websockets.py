from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, Cookie, Query
from starlette.websockets import WebSocket

ws_router = APIRouter()
controller = 'ws_controller'

@ws_router.websocket(
    "/notifications"
)
@inject
async def chat(
    websocket: WebSocket,
    token: str = Query(),
    refresh_token: str = Cookie(),  # Even though the value isn't read it makes sure that the client has a refresh token
    chat_controller: IWebsocketController = Depends(Provide[controller])
):
    await chat_controller.chat(websocket, token)


@ws_router.websocket(
    "/controller"
)
@inject
async def chat(
    websocket: WebSocket,
    token: str = Query(),
    refresh_token: str = Cookie(),  # Even though the value isn't read it makes sure that the client has a refresh token
    chat_controller: IWebsocketController = Depends(Provide[controller])
):
    await chat_controller.chat(websocket, token)
