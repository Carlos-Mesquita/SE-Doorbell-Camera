from fastapi import APIRouter, Depends, HTTPException, status, Request

from ..dtos import FCMDeviceRegistrationDTO
from ..services import IDeviceService
from ..middlewares import OAuth2Authorized

from dependency_injector.wiring import inject, Provide

device_router = APIRouter()
device_service_provider_name = "device_service" 

@device_router.post(
    "/fcm/register",
)
@inject
async def register_fcm_device(
    request: Request,
    request_data: FCMDeviceRegistrationDTO,
    device_service: IDeviceService = Depends(Provide[device_service_provider_name])
):
    user_id_from_token = int(request.user.identity)
    try:
        await device_service.register_or_update_fcm_device(
            user_id=user_id_from_token,
            fcm_token=request_data.fcm_token,
            physical_device_id=request_data.physical_device_id,
            device_type=request_data.device_type,
            app_version=request_data.app_version
        )
        return {"status": "success", "message": "FCM device registered successfully"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to register FCM device: {str(e)}")
