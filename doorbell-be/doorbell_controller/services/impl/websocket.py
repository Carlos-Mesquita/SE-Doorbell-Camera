import json
import asyncio
import websockets

from logging import getLogger
from typing import Dict, List, Callable, Optional, Union, Awaitable

from doorbell_core.models import Message, MessageType


class WebSocketClient:

    def __init__(self, server_url: str, api_key: str):
        self._server_url = server_url
        self._api_key = api_key
        self.connected = False
        self._message_handlers: Dict[MessageType, List[Callable]] = {}
        self._response_futures: Dict[str, asyncio.Future[Message]] = {}
        self._logger = getLogger(__name__)
        self._ws = None
        self._task = None

    def register_handler(self, msg_type: MessageType, handler: Callable[[Message], Union[None, Awaitable[None]]]):
        """
        Register a message handler that can be either synchronous or asynchronous.

        Args:
            msg_type: Type of message to handle
            handler: Function to call with message (can be a coroutine function)
        """
        if msg_type not in self._message_handlers:
            self._message_handlers[msg_type] = []
        self._message_handlers[msg_type].append(handler)

    async def _handle_message(self, message: Message):
        """
        Handle an incoming message.

        Args:
            message: Message to handle
        """
        # Handle response futures first
        if message.reply_to and message.reply_to in self._response_futures:
            future = self._response_futures.pop(message.reply_to)
            future.set_result(message)

        # Then handle registered handlers
        if message.msg_type in self._message_handlers:
            for handler in self._message_handlers[message.msg_type]:
                try:
                    result = handler(message)
                    # Check if the handler is a coroutine and await it if so
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as e:
                    self._logger.error(f"Error in message handler: {e}")

    async def connect(self):
        self._logger.info(f"Connecting to {self._server_url}")
        self._ws = await websockets.connect(self._server_url)

        auth_msg = Message(
            msg_type=MessageType.AUTH,
            payload={"token": self._api_key}
        )

        await self._ws.send(auth_msg.model_dump_json())

        auth_result = await self._ws.recv()
        auth_result = Message(**json.loads(auth_result))

        if auth_result.msg_type != MessageType.AUTH_RESULT:
            error = auth_result.payload.get("error", "Unknown authentication error")
            self._logger.error(f"Authentication failed: {error}")
            await self._ws.close()
            raise ValueError(f"Authentication failed: {error}")

        self._logger.info("Connected and authenticated successfully")
        self.connected = True

        # Start listener task
        self._task = asyncio.create_task(self._listener())

    async def _listener(self):
        """Listen for incoming messages."""
        try:
            while self.connected and self._ws.open:
                try:
                    message = await self._ws.recv()
                    msg_obj = Message(**json.loads(message))
                    await self._handle_message(msg_obj)
                except websockets.exceptions.ConnectionClosed:
                    self._logger.warning("WebSocket connection closed")
                    self.connected = False
                    break
                except Exception as e:
                    self._logger.error(f"Error processing message: {e}")
        except asyncio.CancelledError:
            self._logger.info("WebSocket listener task cancelled")
        finally:
            self.connected = False

    async def disconnect(self):
        """Disconnect from the WebSocket server."""
        if self._task:
            self._task.cancel()
            self._task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        self.connected = False
        self._logger.info("Disconnected from WebSocket server")

    async def send_message(self, message: Message):
        """
        Send a message to the server.

        Args:
            message: Message to send
        """
        if not self.connected or not self._ws:
            raise ConnectionError("Not connected to server")

        await self._ws.send(message.model_dump_json())

    async def send_and_wait_response(
            self,
            message: Message,
            expected_type: Optional[MessageType] = None,
            timeout: float = 10.0
    ) -> Message:
        """
        Send a message and wait for a response.

        Args:
            message: Message to send
            expected_type: Expected type of response
            timeout: Timeout in seconds

        Returns:
            Response message
        """
        if not self.connected or not self._ws:
            raise ConnectionError("Not connected to server")

        # Create a future to store the response
        future = asyncio.Future()
        self._response_futures[message.msg_id] = future

        # Send the message
        await self._ws.send(message.model_dump_json())

        # Wait for the response with timeout
        try:
            response = await asyncio.wait_for(future, timeout)

            # Check if the response is of the expected type
            if expected_type and response.msg_type != expected_type:
                self._logger.warning(
                    f"Unexpected response type: {response.msg_type}, expected: {expected_type}"
                )

            return response
        except asyncio.TimeoutError:
            del self._response_futures[message.msg_id]
            raise TimeoutError(f"No response received within {timeout} seconds")
