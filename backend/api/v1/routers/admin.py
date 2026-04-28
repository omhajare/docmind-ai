from fastapi import APIRouter, Header, HTTPException, status

from config import get_settings
from admin.controls import get_ai_enabled, toggle_ai_enabled

settings = get_settings()
router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/status")
async def admin_status():
    return {"ai_enabled": get_ai_enabled()}


@router.post("/toggle")
async def admin_toggle(x_admin_password: str = Header(None)):
    if x_admin_password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin password",
        )
    new_state = toggle_ai_enabled()
    return {"ai_enabled": new_state, "message": f"AI service {'enabled' if new_state else 'disabled'}"}
