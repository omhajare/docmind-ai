"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings

settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

# Rate limit strings
STANDARD_LIMIT = f"{settings.RATE_LIMIT_REQUESTS_PER_MINUTE}/minute"
AI_LIMIT = f"{settings.RATE_LIMIT_AI_REQUESTS_PER_MINUTE}/minute"
