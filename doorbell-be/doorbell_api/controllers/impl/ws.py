import asyncio
import os

from jwt import PyJWTError
from fastapi.websockets import WebSocket

from doorbell_api.exceptions import DecodeTokenException, ExpiredTokenException, NotFoundException
from doorbell_api.services import IAuthService


class WebsocketController:

    def __init__(self,
        #ws_service: IWebsocketService,
        auth_service: IAuthService
    ):
        #self._ws_service = ws_service
        self._auth_service = auth_service

    async def ws(self, websocket: WebSocket, access_token: str):
        closed = False
        try:
            session_id = await self._auth_service.decode_token(access_token)

            await websocket.accept()
            while True:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=int(os.getenv("WEBSOCKET_TIMEOUT")))
                try:
                    # call service here
                    pass
                except ValueError as e:
                    print(e)
                    await websocket.send_text("Invalid message format!")
        except (PyJWTError, DecodeTokenException, ExpiredTokenException):
            closed = True
            await websocket.close(code=4001, reason="Unauthorized!")
        except NotFoundException as e:
            closed = True
            await websocket.close(code=4004, reason=e.message)
        except asyncio.TimeoutError:
            closed = True
            await websocket.close(code=4008, reason="Connection timeout!")
        finally:
            if not closed:
                await websocket.close(code=4500, reason="Unknown error!")
