from http import HTTPStatus
from typing import Optional


class CustomAPIException(Exception):
    code = HTTPStatus.INTERNAL_SERVER_ERROR
    message = HTTPStatus.INTERNAL_SERVER_ERROR.description

    def __init__(self, custom_msg: Optional[str] = None):
        if custom_msg:
            self.message = custom_msg
