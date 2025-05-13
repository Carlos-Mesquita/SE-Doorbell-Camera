import asyncio
import json
import os
import uuid

from asyncio import Queue
from logging import getLogger
from typing import Coroutine, Callable, Dict, Any

from jwt import PyJWTError
from fastapi import WebSocket, WebSocketDisconnect

from doorbell_api.controllers import IWebSocketController
from doorbell_api.exceptions import DecodeTokenException, ExpiredTokenException, ForbiddendWS
from doorbell_api.services import IAuthService, IMessageHandler, IWebRTCSignalingService


class WebsocketController(IWebSocketController):

    def __init__(self,
        auth_service: IAuthService,
        message_handler: IMessageHandler,
        signaling_service: IWebRTCSignalingService,
        message_queue: Queue
    ):
        self._auth_service = auth_service
        self._signaling_service = signaling_service
        self._message_handler = message_handler
        self._message_queue = message_queue
        self._logger = getLogger(__name__)

    async def handle_camera_events(self, websocket: WebSocket, access_token: str):
        await self._handle_ws(websocket, access_token, self._message_handler.handle_camera_events)

    async def _handle_ws(
            self, websocket: WebSocket, access_token: str,
            process: Callable[[any, Dict[str, any], Queue], Coroutine[Any, Any, dict[str, Any]]]
    ):
        try:
            jwt_payload = await self._auth_service.decode_token(access_token)
            await websocket.accept()
            while True:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=int(os.getenv("WEBSOCKET_TIMEOUT")))
                reply = await process(message, jwt_payload, self._message_queue)
                await websocket.send_text(json.dumps(reply))
        except WebSocketDisconnect:
            # starlette takes care of this with a 1000
            self._logger.info("WebSocket disconnected")
        except (PyJWTError, DecodeTokenException, ExpiredTokenException) as e:
            await websocket.close(code=3000, reason=e.message)
        except ForbiddendWS as e:
            await websocket.close(code=3003, reason=e.message)
        except asyncio.TimeoutError:
            await websocket.close(code=3008, reason="Connection timeout!")
        except Exception as e:
            self._logger.error(f"WebSocket error: {str(e)}")
            await websocket.close(code=1011, reason="Internal server error")

    async def handle_signaling(self, websocket: WebSocket, access_token: str):
        try:
            user_id = await self._auth_service.decode_token(access_token)

            await websocket.accept()
            client_id = str(uuid.uuid4())

            await self._signaling_service.register_client(client_id, websocket, user_id)

            await websocket.send_text(json.dumps({
                "type": "registered",
                "clientId": client_id
            }))

            closed = False
            try:
                while True:
                    message = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=int(os.getenv("WEBSOCKET_TIMEOUT", "60"))
                    )

                    try:
                        message_data = json.loads(message)
                        response = await self._signaling_service.handle_message(client_id, message_data)
                        await websocket.send_text(json.dumps(response))
                    except json.JSONDecodeError:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Invalid JSON format"
                        }))
                    except Exception as e:
                        self._logger.error(f"Error processing message: {str(e)}")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": f"Error processing message: {str(e)}"
                        }))
            except asyncio.TimeoutError:
                closed = True
                await websocket.close(code=4008, reason="Connection timeout!")
            except Exception as e:
                self._logger.error(f"WebSocket error: {str(e)}")
                closed = True
                await websocket.close(code=4500, reason="Internal server error")
            finally:
                await self._signaling_service.unregister_client(client_id)
                if not closed:
                    await websocket.close(code=1000, reason="Connection closed normally")

        except (PyJWTError, DecodeTokenException, ExpiredTokenException):
            raise ForbiddendWS()
