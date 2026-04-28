import json
from database.db_client import get_db


# ─── Sessions ────────────────────────────────────────────────

def create_session(user_id: str, title: str = "New Chat") -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_sessions (user_id, title)
                VALUES (%s, %s)
                RETURNING id, user_id, title, created_at, updated_at
                """,
                (user_id, title),
            )
            return dict(cur.fetchone())


def find_sessions_by_user(user_id: str) -> list[dict]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, title, created_at, updated_at
                FROM chat_sessions WHERE user_id = %s ORDER BY updated_at DESC
                """,
                (user_id,),
            )
            return [dict(row) for row in cur.fetchall()]


def find_session_by_id(session_id: str) -> dict | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_sessions WHERE id = %s", (session_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def count_sessions_by_user(user_id: str) -> int:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM chat_sessions WHERE user_id = %s", (user_id,))
            return cur.fetchone()["cnt"]


def update_session_title(session_id: str, title: str) -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE chat_sessions SET title = %s, updated_at = NOW()
                WHERE id = %s RETURNING id, user_id, title, created_at, updated_at
                """,
                (title, session_id),
            )
            return dict(cur.fetchone())


def update_session_timestamp(session_id: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE chat_sessions SET updated_at = NOW() WHERE id = %s", (session_id,))


def delete_session(session_id: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_sessions WHERE id = %s", (session_id,))


# ─── Messages ────────────────────────────────────────────────

def save_message(
    session_id: str,
    user_id: str,
    role: str,
    content: str,
    sources: dict | None = None,
    tools_used: list | None = None,
    confidence: str | None = None,
) -> dict:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO chat_messages (session_id, user_id, role, content, sources, tools_used, confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, session_id, user_id, role, content, sources, tools_used, confidence, created_at
                """,
                (
                    session_id,
                    user_id,
                    role,
                    content,
                    json.dumps(sources) if sources else None,
                    json.dumps(tools_used) if tools_used else None,
                    confidence,
                ),
            )
            return dict(cur.fetchone())


def get_messages(session_id: str, limit: int = 10, offset: int = 0) -> list[dict]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, session_id, role, content, sources, tools_used, confidence, created_at
                FROM chat_messages WHERE session_id = %s
                ORDER BY created_at ASC LIMIT %s OFFSET %s
                """,
                (session_id, limit, offset),
            )
            return [dict(row) for row in cur.fetchall()]


def get_recent_messages(session_id: str, limit: int = 10) -> list[dict]:
    """Get the most recent messages for context window (ordered oldest-first)."""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT role, content FROM (
                    SELECT role, content, created_at FROM chat_messages
                    WHERE session_id = %s ORDER BY created_at DESC LIMIT %s
                ) sub ORDER BY created_at ASC
                """,
                (session_id, limit),
            )
            return [dict(row) for row in cur.fetchall()]


def find_message_by_id(message_id: str) -> dict | None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM chat_messages WHERE id = %s", (message_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def delete_message(message_id: str) -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM chat_messages WHERE id = %s", (message_id,))
