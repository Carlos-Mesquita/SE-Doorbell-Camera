from http import HTTPStatus
from .base import CustomAPIException


class UnauthorizedException(CustomAPIException):
    code = HTTPStatus.UNAUTHORIZED
    message = HTTPStatus.UNAUTHORIZED.description

class DecodeTokenException(CustomAPIException):
    code = HTTPStatus.UNAUTHORIZED
    message = "No permission -- invalid signature"

class ExpiredTokenException(CustomAPIException):
    code = HTTPStatus.UNAUTHORIZED
    message = "No permission -- expired token"

class ForbiddendWS(CustomAPIException):
    code = HTTPStatus.UNAUTHORIZED
    message = "No permission -- invalid token"
