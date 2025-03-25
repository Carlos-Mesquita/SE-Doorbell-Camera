from http import HTTPStatus

from doorbell_api.exceptions import CustomAPIException


class NotFoundException(CustomAPIException):
    code = HTTPStatus.NOT_FOUND
    message = HTTPStatus.NOT_FOUND.description
