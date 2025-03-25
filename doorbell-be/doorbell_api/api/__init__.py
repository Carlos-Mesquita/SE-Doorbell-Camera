from fastapi import APIRouter

from .auth import auth_router
from .capture import capture_router
from .notification import notification_router
from .settings import settings_router

router = APIRouter(prefix="/api")

@router.get('/healthcheck')
async def healthcheck():
    return {"healthy": True}

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(capture_router, prefix="/capture", tags=["Captures"])
router.include_router(notification_router, prefix="/notification", tags=["Notifications"])
router.include_router(settings_router, prefix="/settings", tags=["Settings"])
