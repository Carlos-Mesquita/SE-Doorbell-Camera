import asyncio
import json
from uuid import uuid4
from logging import getLogger
from typing import Coroutine, Callable, Dict, Any, Optional  # Added Optional
from jwt import PyJWTError
from fastapi import WebSocket, WebSocketDisconnect
from dependency_injector.wiring import Provide, inject

from ...configs.db.context import orm_session_context
from ...controllers import IWebSocketController  # Adjust import
from ...exceptions import DecodeTokenException, ExpiredTokenException, ForbiddendWS  # Adjust import
from ...services import IAuthService, IMessageHandler, IWebRTCSignalingService  # Adjust import
from doorbell_shared.models import Message, MessageTypeJSONEncoder  # Assuming this path is correct for shared models


class WebsocketController(IWebSocketController):
    @inject
    def __init__(self,
        auth_service: IAuthService = Provide['auth_service'],
        message_handler: IMessageHandler = Provide['message_handler'],
        signaling_service: IWebRTCSignalingService = Provide['signaling_service'],
    ):
        self._auth_service = auth_service
        self._signaling_service = signaling_service
        self._message_handler = message_handler
        self._logger = getLogger(__name__)

    async def handle_camera_events(self, websocket: WebSocket, access_token: str):
        await self._handle_ws(websocket, access_token, self._message_handler.handle_camera_events)

    async def _handle_ws(
            self, websocket: WebSocket, access_token: str,
            process: Callable[[Message, Dict[str, any]], Coroutine[Any, Any, Optional[Dict[str, Any]]]]
    ):
        context_token = orm_session_context.set(str(uuid4()))
        connection_id = str(uuid4())
        client_info_str = f"{websocket.client.host}:{websocket.client.port}"  # For logging
        self._logger.info(f"WS conn {connection_id} attempt from {client_info_str} for endpoint.")

        try:
            jwt_payload = await self._auth_service.decode_token(access_token)
            await websocket.accept()
            self._logger.info(
                f"WS conn {connection_id} accepted for user {jwt_payload.get('sub', 'unknown')} from {client_info_str}")

            while True:
                message_str = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=None
                )
                self._logger.debug(f"WS conn {connection_id} received raw: {message_str[:200]}")

                try:
                    message_obj = Message(**json.loads(message_str))
                except (json.JSONDecodeError, Exception) as e:
                    self._logger.warning(f"WS conn {connection_id}: Invalid message: {e} - Data: {message_str[:200]}")
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": f"Invalid message format/structure: {e}"}))
                    continue

                reply_dict = await process(message_obj, jwt_payload)

                if reply_dict:
                    await websocket.send_text(json.dumps(reply_dict, cls=MessageTypeJSONEncoder))
                    self._logger.debug(f"WS conn {connection_id} sent reply: {str(reply_dict)[:200]}")

        except WebSocketDisconnect:
            self._logger.info(f"WS conn {connection_id} from {client_info_str} disconnected.")
        except (PyJWTError, DecodeTokenException, ExpiredTokenException) as e:
            self._logger.warning(f"WS conn {connection_id} auth error for {client_info_str}: {e}")
            await websocket.close(code=3000, reason=str(e))
        except ForbiddendWS as e:
            self._logger.warning(f"WS conn {connection_id} forbidden for {client_info_str}: {e}")
            await websocket.close(code=3003, reason=str(e))
        except asyncio.TimeoutError:
            self._logger.info(f"WS conn {connection_id} from {client_info_str} timed out.")
            await websocket.close(code=3008, reason="Connection timeout!")
        except Exception as e:
            self._logger.error(f"WS conn {connection_id} from {client_info_str} unexpected error: {e}", exc_info=True)
        finally:
            orm_session_context.reset(context_token)
            self._logger.info(f"WS conn {connection_id} from {client_info_str} processing ended.")

    async def handle_signaling(self, websocket: WebSocket, access_token: str):
        context_token = orm_session_context.set(str(uuid4()))
        connection_id = str(uuid4())
        client_info_str = f"{websocket.client.host}:{websocket.client.port}"
        self._logger.info(f"WebRTC signaling conn {connection_id} attempt from {client_info_str}")

        try:
            jwt_payload = await self._auth_service.decode_token(access_token)
            user_id_from_token = jwt_payload.get('sub')
            if not user_id_from_token:
                raise ForbiddendWS("User identifier not found in token.")

            await websocket.accept()
            self._logger.info(
                f"WebRTC conn {connection_id} accepted for user {user_id_from_token} from {client_info_str}")

            await self._signaling_service.register_client(connection_id, websocket, user_id_from_token)

            await websocket.send_text(json.dumps({
                "type": "registered",
                "clientId": connection_id
            }))

            while True:
                message_str = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=None
                )
                self._logger.debug(f"WebRTC conn {connection_id} received raw: {message_str[:200]}")

                try:
                    message_data = json.loads(message_str)
                    response = await self._signaling_service.handle_message(connection_id, message_data)
                    if response:
                        await websocket.send_text(json.dumps(response))
                        self._logger.debug(f"WebRTC conn {connection_id} sent response: {str(response)[:200]}")
                except json.JSONDecodeError:
                    self._logger.warning(f"WebRTC conn {connection_id}: Invalid JSON: {message_str[:200]}")
                    await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON format"}))
                except Exception as e:
                    self._logger.error(f"WebRTC conn {connection_id}: Error processing message: {e}", exc_info=True)
                    await websocket.send_text(
                        json.dumps({"type": "error", "message": f"Error processing message: {str(e)}"}))

        except WebSocketDisconnect:
            self._logger.info(f"WebRTC conn {connection_id} from {client_info_str} disconnected.")
        except (PyJWTError, DecodeTokenException, ExpiredTokenException) as e:
            self._logger.warning(f"WebRTC conn {connection_id} auth error for {client_info_str}: {e}")
            await websocket.close(code=3000, reason=str(e))
        except ForbiddendWS as e:
            self._logger.warning(f"WebRTC conn {connection_id} forbidden for {client_info_str}: {e}")
            await websocket.close(code=3003, reason=str(e))
        except asyncio.TimeoutError:
            self._logger.info(f"WebRTC conn {connection_id} from {client_info_str} timed out.")
            await websocket.close(code=4008, reason="Connection timeout!")
        except Exception as e:
            self._logger.error(f"WebRTC conn {connection_id} from {client_info_str} unexpected error: {e}", exc_info=True)
        finally:
            await self._signaling_service.unregister_client(connection_id)
            orm_session_context.reset(context_token)
            self._logger.info(f"WebRTC conn {connection_id} from {client_info_str} processing ended and unregistered.")