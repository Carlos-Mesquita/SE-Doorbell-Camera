import json
import asyncio
import websockets

from asyncio import create_task, CancelledError, Future, wait_for, iscoroutine
from logging import getLogger
from typing import Dict, List, Callable, Optional, Union, Awaitable

from doorbell_shared.models import Message, MessageType


class WebSocketClient:

    def __init__(self, ws_url: str, ws_endpoint: str, token: str, message_handler=True):
        self._ws_url = f"{ws_url}/{ws_endpoint}"
        self._token = token
        self.connected = False
        self._message_handlers: Dict[MessageType, List[Callable]] = {}
        self._response_futures: Dict[str, Future[Message]] = {}
        self._logger = getLogger(__name__)
        self._ws = None
        self._task = None
        self._message_handler = message_handler

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
                    if iscoroutine(result):
                        await result
                except Exception as e:
                    self._logger.error(f"Error in message handler: {e}")

    async def connect(self):
        self._logger.info(f"Connecting to {self._ws_url}")
        self._ws = await websockets.connect(f"{self._ws_url}?token={self._token}")

        self._logger.info("Connected and authenticated successfully")
        self.connected = True

        if self._message_handler:
            self._task = asyncio.create_task(self._listener())
        else:
            return self._ws

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
        except CancelledError:
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
        future = Future()
        self._response_futures[message.msg_id] = future

        # Send the message
        await self._ws.send(message.model_dump_json())

        # Wait for the response with timeout
        try:
            response = await wait_for(future, timeout)

            # Check if the response is of the expected type
            if expected_type and response.msg_type != expected_type:
                self._logger.warning(
                    f"Unexpected response type: {response.msg_type}, expected: {expected_type}"
                )

            return response
        except asyncio.TimeoutError:
            del self._response_futures[message.msg_id]
            raise TimeoutError(f"No response received within {timeout} seconds")
