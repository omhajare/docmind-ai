import hashlib
from datetime import datetime, timedelta, timezone

from database.db_client import get_db


def _hash_token(token: str) -> str:
    """SHA-256 hash of a raw token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ─── Refresh Tokens ──────────────────────────────────────────

def create_refresh_token(user_id: str, raw_token: str, expire_days: int) -> dict:
    """Store a hashed refresh token."""
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=expire_days)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, expires_at, created_at
                """,
                (user_id, token_hash, expires_at),
            )
            return dict(cur.fetchone())


def find_refresh_token(raw_token: str) -> dict | None:
    """Look up a refresh token by its hash."""
    token_hash = _hash_token(raw_token)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM refresh_tokens
                WHERE token_hash = %s AND is_revoked = FALSE AND expires_at > NOW()
                """,
                (token_hash,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def revoke_refresh_token(raw_token: str) -> None:
    """Mark a refresh token as revoked."""
    token_hash = _hash_token(raw_token)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE refresh_tokens SET is_revoked = TRUE WHERE token_hash = %s",
                (token_hash,),
            )


def revoke_all_user_tokens(user_id: str) -> None:
    """Revoke all refresh tokens for a user."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE refresh_tokens SET is_revoked = TRUE WHERE user_id = %s AND is_revoked = FALSE",
                (user_id,),
            )


# ─── Password Reset Tokens ──────────────────────────────────

def create_reset_token(user_id: str, raw_token: str, expire_minutes: int) -> dict:
    """Store a hashed password reset token."""
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                RETURNING id, user_id, expires_at
                """,
                (user_id, token_hash, expires_at),
            )
            return dict(cur.fetchone())


def find_reset_token(raw_token: str) -> dict | None:
    """Look up a valid (unused, not expired) password reset token."""
    token_hash = _hash_token(raw_token)
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM password_reset_tokens
                WHERE token_hash = %s AND used = FALSE AND expires_at > NOW()
                """,
                (token_hash,),
            )
            row = cur.fetchone()
            return dict(row) if row else None


def mark_reset_token_used(token_id: str) -> None:
    """Mark a password reset token as used."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE password_reset_tokens SET used = TRUE WHERE id = %s",
                (token_id,),
            )
