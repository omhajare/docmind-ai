from database.db_client import get_db
from utils.logger import logger


def find_by_email(email: str) -> dict | None:
    """Find a user by email. Returns dict or None."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            return dict(row) if row else None


def find_by_id(user_id: str) -> dict | None:
    """Find a user by ID."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def create(email: str, password_hash: str, full_name: str) -> dict:
    """Insert a new user and return the created record."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (email, password_hash, full_name)
                VALUES (%s, %s, %s)
                RETURNING id, email, full_name, created_at
                """,
                (email, password_hash, full_name),
            )
            return dict(cur.fetchone())


def update_last_login(user_id: str) -> None:
    """Set last_login to NOW() for the given user."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s",
                (user_id,),
            )


def update_password(user_id: str, new_password_hash: str) -> None:
    """Update the user's password hash."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = NOW() WHERE id = %s",
                (new_password_hash, user_id),
            )
