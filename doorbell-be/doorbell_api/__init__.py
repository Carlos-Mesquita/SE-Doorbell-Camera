import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from doorbell_api.api import router
from doorbell_api.middlewares import setup_middlewares
from doorbell_api.exceptions import setup_exception_handlers



@asynccontextmanager
async def lifespan(_app: FastAPI):

    yield


def create_app() -> FastAPI:
    env = os.getenv("ENV")
    _app = FastAPI(
        docs_url="/docs" if env != "production" else None,
        redoc_url="/redoc" if env != "production" else None,
        middleware=setup_middlewares(),
        lifespan=lifespan
    )
    _app.include_router(router)
    setup_exception_handlers(_app)
    return _app


app = create_app()
