from collections import defaultdict
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .base import CustomAPIException


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def custom_form_validation_error(_, exc: RequestValidationError):
        reformatted_message = defaultdict(list)
        for pydantic_error in exc.errors():
            loc, msg = pydantic_error["loc"], pydantic_error["msg"]
            filtered_loc = loc[1:] if loc[0] in ("body", "query", "path") else loc
            field_string = ".".join(filtered_loc)
            if field_string == "cookie.refresh_token":
                code, _, description = HTTPStatus.UNAUTHORIZED
                return JSONResponse(
                    status_code=code,
                    content={"message": description},
                )
            reformatted_message[field_string].append(msg)

        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST.value,
            content=jsonable_encoder(
                {"details": "Invalid request!", "errors": reformatted_message}
            ),
        )

    @app.exception_handler(CustomAPIException)
    async def custom_exception_handler(_, exc: CustomAPIException):
        return JSONResponse(
            status_code=exc.code,
            content={"message": exc.message},
        )

    @app.exception_handler(Exception)
    async def default_exception_handler(_, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=str(exc),
        )
