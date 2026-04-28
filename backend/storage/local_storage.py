import os
import uuid
from pathlib import Path

from utils.logger import logger

UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


def save_file(user_id: str, filename: str, content: bytes) -> str:
    """Save file to local uploads/ folder. Returns the storage path."""
    user_dir = UPLOADS_DIR / user_id
    user_dir.mkdir(parents=True, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = user_dir / safe_name
    file_path.write_bytes(content)

    storage_path = f"{user_id}/{safe_name}"
    logger.info(f"Saved file locally: {storage_path}")
    return storage_path


def delete_file(storage_path: str) -> None:
    """Delete a file from local uploads/ folder."""
    file_path = UPLOADS_DIR / storage_path
    if file_path.exists():
        file_path.unlink()
        logger.info(f"Deleted local file: {storage_path}")
    else:
        logger.warning(f"File not found for deletion: {storage_path}")


def get_full_path(storage_path: str) -> str:
    """Get the absolute path for a stored file."""
    return str(UPLOADS_DIR / storage_path)
