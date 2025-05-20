import os
import firebase_admin
from contextlib import asynccontextmanager
from fastapi import FastAPI
from firebase_admin import credentials

from .api import router
from .configs import DependencyInjector
from .middlewares import setup_middlewares
from .exceptions import setup_exception_handlers



@asynccontextmanager
async def lifespan(_app: FastAPI):
    cred = credentials.Certificate('./doorbell_api/firebase_credentials.json')
    firebase_admin.initialize_app(cred)
    yield


def create_app() -> FastAPI:
    env = os.getenv("ENV")
    _app = FastAPI(
        docs_url="/docs" if env != "production" else None,
        redoc_url="/redoc" if env != "production" else None,
        middleware=setup_middlewares(),
        lifespan=lifespan
    )
    DependencyInjector().inject()
    _app.include_router(router)
    setup_exception_handlers(_app)
    return _app


app = create_app()
