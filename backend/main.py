from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database.db_client import init_db
from middleware.rate_limiter import limiter
from utils.logger import logger

from api.v1.routers.health import router as health_router
from api.v1.routers.auth import router as auth_router
from api.v1.routers.documents import router as documents_router
from api.v1.routers.chat import router as chat_router
from api.v1.routers.research import router as research_router
from api.v1.routers.admin import router as admin_router

settings = get_settings()

app = FastAPI(
    title="DocMind AI",
    description="AI Research & Synthesis Agent — Backend API",
    version=settings.APP_VERSION,
)

# ─── Rate Limiter ────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


# ─── Security Headers ───────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response

# ─── Routers ─────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(health_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(documents_router, prefix=API_PREFIX)
app.include_router(chat_router, prefix=API_PREFIX)
app.include_router(research_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)


# ─── Startup Event ───────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting DocMind AI v{settings.APP_VERSION} [{settings.ENVIRONMENT}]")
    init_db()
    logger.info("Database tables initialized")

    # Stale job recovery — mark stuck jobs as failed
    from repositories.research_repository import mark_stale_jobs_failed, cleanup_expired_jobs
    stale_count = mark_stale_jobs_failed()
    if stale_count > 0:
        logger.info(f"Marked {stale_count} stale research job(s) as failed")

    # Retention cleanup — delete expired jobs
    expired_count = cleanup_expired_jobs()
    if expired_count > 0:
        logger.info(f"Cleaned up {expired_count} expired research job(s)")
