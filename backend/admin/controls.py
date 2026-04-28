"""App settings read/write helpers."""

from database.db_client import get_db


def get_ai_enabled() -> bool:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM app_settings WHERE key = 'ai_enabled'")
            row = cur.fetchone()
            return row["value"] == "true" if row else True


def toggle_ai_enabled() -> bool:
    """Toggle AI service and return new state."""
    current = get_ai_enabled()
    new_value = "false" if current else "true"
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE app_settings SET value = %s WHERE key = 'ai_enabled'",
                (new_value,),
            )
    return not current
