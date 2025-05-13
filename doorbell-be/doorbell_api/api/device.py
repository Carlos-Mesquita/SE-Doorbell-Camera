from fastapi import APIRouter


device_router = APIRouter()
controller_name = "device_controller"

"""
@device_router.post("/register")
async def register_device(
    request: DeviceRegistrationRequest,
    current_user=Depends(get_current_user)  # Your auth dependency
):
    if request.user_id != current_user.id:
        raise HTTPException(status_code=403, forbidden="User ID mismatch")

    # Upsert the device registration (update if exists, insert if not)
    await db.devices.update_one(
        {"user_id": request.user_id, "device_id": request.device_id},
        {"$set": {
            "fcm_token": request.fcm_token,
            "updated_at": datetime.now()
        }},
        upsert=True
    )

    return {"status": "success"}
"""