import bcrypt

from config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_WORK_FACTOR)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash (constant-time)."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
