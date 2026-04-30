from datetime import datetime, timezone

from fastapi import APIRouter

from config import get_settings

router = APIRouter()
settings = get_settings()


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check():
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
