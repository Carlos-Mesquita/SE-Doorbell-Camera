import json
from typing import Callable, Dict, Type
from fastapi import WebSocket

class WebSocketExceptionHandler:
    def __init__(self):
        self.exception_handlers: Dict[Type[Exception], Callable] = {}

    def register(self, exc_class: Type[Exception]):
        def decorator(func: Callable):
            self.exception_handlers[exc_class] = func
            return func
        return decorator

    async def handle_exception(self, websocket: WebSocket, exc: Exception):
        exc_type = type(exc)
        handler = self.exception_handlers.get(exc_type)

        if handler:
            await handler(websocket, exc)
        else:
            await websocket.send_text(json.dumps({"error": str(exc)}))
            await websocket.close(code=1011)
