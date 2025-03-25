from functools import wraps
from typing import Type

from .base import CustomAPIException

class CatchesAndThrows:
    def __init__(self,
        catch_exception: Type[Exception],
        response_exception_class: Type[CustomAPIException],
        message: str
    ):
        self._catch_exception = catch_exception
        self._response_exception_class = response_exception_class
        self._message = message

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except self._catch_exception:
                raise self._response_exception_class(self._message)
        return wrapper
