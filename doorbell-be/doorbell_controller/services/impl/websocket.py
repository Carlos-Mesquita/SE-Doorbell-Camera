import json
import asyncio
import websockets

from asyncio import CancelledError, Future, wait_for, \
    iscoroutine
from logging import getLogger
from typing import Dict, List, Callable, Optional, Union, Awaitable, Any

from doorbell_shared.models import Message, MessageType


class WebSocketClient:

    def __init__(self, ws_url: str, ws_endpoint: str, token: str, message_handler=True):
        self._base_ws_url = ws_url
        self._ws_endpoint = ws_endpoint
        self._token = token
        self.connected = False
        self._message_handlers: Dict[MessageType, List[Callable[[Message], Union[None, Awaitable[None]]]]] = {}
        self._response_futures: Dict[str, Future[Message]] = {}
        self._logger = getLogger(__name__)
        self._ws: Optional[Any] = None
        self._listener_task: Optional[asyncio.Task] = None
        self._should_run_message_handler = message_handler

    def register_handler(self, msg_type: MessageType, handler: Callable[[Message], Union[None, Awaitable[None]]]):
        if not isinstance(msg_type, MessageType):
            self._logger.error(f"Attempted to register handler for non-MessageType: {msg_type}")
            return
        if msg_type not in self._message_handlers:
            self._message_handlers[msg_type] = []
        self._message_handlers[msg_type].append(handler)

    def _is_websocket_open(self) -> bool:
        return self._ws is not None and getattr(self._ws, 'state', 0) == 1

    async def _handle_message(self, message_str: str):
        try:
            msg_obj = Message(**json.loads(message_str))
        except json.JSONDecodeError:
            self._logger.error(f"Failed to decode JSON message: {message_str}")
            return
        except Exception as e:
            self._logger.error(f"Error creating Message object from JSON: {e} - Data: {message_str}")
            return

        if msg_obj.reply_to and msg_obj.reply_to in self._response_futures:
            future = self._response_futures.pop(msg_obj.reply_to)
            if not future.done():
                future.set_result(msg_obj)
            else:
                self._logger.warning(f"Future for {msg_obj.reply_to} was already done.")

        if msg_obj.msg_type in self._message_handlers:
            for handler in self._message_handlers[msg_obj.msg_type]:
                try:
                    result = handler(msg_obj)
                    if iscoroutine(result):
                        await result
                except Exception as e:
                    self._logger.error(f"Error in message handler for {msg_obj.msg_type}: {e}", exc_info=True)

    async def connect(self) -> Optional[asyncio.Task]:
        if self.connected:
            self._logger.info("Already connected.")
            return self._listener_task

        if self._listener_task and not self._listener_task.done():
            self._logger.info("Cancelling previous listener task...")
            old_connected_state = self.connected
            self._listener_task.cancel()
            try:
                await self._listener_task
            except CancelledError:
                pass
            self._listener_task = None
            self.connected = old_connected_state

        full_ws_url = f"{self._base_ws_url}/{self._ws_endpoint}?token={self._token}"
        self._logger.info(f"Connecting to {full_ws_url}")
        try:
            self._ws = await websockets.connect(full_ws_url, open_timeout=10)
        except Exception as e:
            self._logger.error(f"Failed to connect to {full_ws_url}: {e}")
            self.connected = False
            self._ws = None
            return None

        self._logger.info("Connected and authenticated successfully")
        self._logger.info(f"WebSocket state after connect: {getattr(self._ws, 'state', 'unknown')}")

        # Small delay to see if connection stays open
        await asyncio.sleep(0.1)
        self._logger.info(f"WebSocket state after 100ms: {getattr(self._ws, 'state', 'unknown')}")

        if not self._is_websocket_open():
            self._logger.error("WebSocket connection is not open!")
            return None

        self.connected = True

        if self._should_run_message_handler:
            self._listener_task = asyncio.create_task(self._listener(), name=f"WSListener_{self._ws_endpoint}")
            return self._listener_task
        else:
            self._logger.warning(
                "WebSocketClient created with message_handler=False. Raw WebSocket returned from connect().")
            return None

    async def _listener(self):
        self._logger.info(f"_listener starting - connected: {self.connected}, ws_open: {self._is_websocket_open()}")
        self._logger.info(
            f"WebSocket state in listener: {getattr(self._ws, 'state', 'unknown') if self._ws else 'None'}")

        try:
            while self.connected and self._is_websocket_open():
                self._logger.debug("About to call recv()")
                try:
                    message_str = await self._ws.recv()
                    await self._handle_message(message_str)
                except websockets.exceptions.ConnectionClosedOK:
                    self._logger.info("WebSocket connection closed normally.")
                    break
                except websockets.exceptions.ConnectionClosedError as e:
                    self._logger.warning(f"WebSocket connection closed with error: {e}")
                    break
                except CancelledError:
                    self._logger.info("WebSocket listener task cancelled.")
                    raise
                except Exception as e:
                    self._logger.error(f"Error processing message in listener: {e}", exc_info=True)
                    if not self.connected or not self._is_websocket_open():
                        break

            self._logger.info(f"Exited while loop - connected: {self.connected}, ws_open: {self._is_websocket_open()}")

        except CancelledError:
            self._logger.info("WebSocket listener task was cancelled (outer).")
        finally:
            self._logger.info(f"WebSocket listener for {self._ws_endpoint} stopped.")
            # Only set connected = False if WebSocket is actually closed, not if task was just cancelled
            if not self._is_websocket_open():
                self.connected = False

    async def disconnect(self):
        self._logger.info(f"Disconnecting from WebSocket server {self._base_ws_url}/{self._ws_endpoint}...")
        if self._listener_task and not self._listener_task.done():
            self._listener_task.cancel()
            try:
                await self._listener_task
            except CancelledError:
                self._logger.info("Listener task successfully cancelled during disconnect.")
            except Exception as e:
                self._logger.error(f"Error waiting for listener task during disconnect: {e}", exc_info=True)
        self._listener_task = None

        if self._ws and self._is_websocket_open():
            try:
                await self._ws.close()
                self._logger.info("WebSocket connection closed.")
            except Exception as e:
                self._logger.error(f"Error closing WebSocket: {e}", exc_info=True)

        self._ws = None
        self.connected = False

        for msg_id, future in list(self._response_futures.items()):
            if not future.done():
                future.cancel("WebSocket disconnected")
            del self._response_futures[msg_id]
        self._logger.info(f"Disconnected from WebSocket server {self._base_ws_url}/{self._ws_endpoint}.")

    async def send_message(self, message: Message):
        if not self.connected or not self._is_websocket_open():
            self._logger.error("Not connected to server, cannot send message.")
            raise ConnectionError("Not connected to server")

        try:
            await self._ws.send(message.model_dump_json())
        except websockets.exceptions.ConnectionClosed:
            self._logger.error("Failed to send message: Connection closed.")
            self.connected = False
            raise ConnectionError("Connection closed while sending message")
        except Exception as e:
            self._logger.error(f"Error sending message: {e}", exc_info=True)
            raise

    async def send_and_wait_response(
            self,
            message: Message,
            timeout: float = 10.0
    ) -> Message:
        if not self.connected or not self._is_websocket_open():
            self._logger.error("Not connected to server, cannot send message and wait for response.")
            raise ConnectionError("Not connected to server")

        future: Future[Message] = asyncio.get_running_loop().create_future()
        self._response_futures[message.msg_id] = future

        try:
            await self.send_message(message)
        except Exception as e:
            del self._response_futures[message.msg_id]
            raise

        try:
            response = await wait_for(future, timeout)
            return response
        except asyncio.TimeoutError:
            self._logger.warning(f"Timeout waiting for response to message {message.msg_id}")
            if message.msg_id in self._response_futures:
                del self._response_futures[message.msg_id]
            raise
        except CancelledError:
            self._logger.info(f"send_and_wait_response for {message.msg_id} cancelled.")
            if message.msg_id in self._response_futures:
                del self._response_futures[message.msg_id]
            raise
