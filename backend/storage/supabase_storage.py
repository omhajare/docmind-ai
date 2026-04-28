import uuid

from config import get_settings
from utils.logger import logger

settings = get_settings()


def _get_client():
    from supabase import create_client
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


BUCKET_NAME = "docmind"


def save_file(user_id: str, filename: str, content: bytes) -> str:
    """Upload file to Supabase Storage. Returns the storage path."""
    client = _get_client()
    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    storage_path = f"{user_id}/{safe_name}"

    client.storage.from_(BUCKET_NAME).upload(
        path=storage_path,
        file=content,
        file_options={"content-type": "application/pdf"},
    )
    logger.info(f"Uploaded to Supabase Storage: {storage_path}")
    return storage_path


def delete_file(storage_path: str) -> None:
    """Delete a file from Supabase Storage."""
    client = _get_client()
    client.storage.from_(BUCKET_NAME).remove([storage_path])
    logger.info(f"Deleted from Supabase Storage: {storage_path}")


def get_full_path(storage_path: str) -> str:
    """For Supabase, return a signed URL (not used in local indexing)."""
    client = _get_client()
    return client.storage.from_(BUCKET_NAME).create_signed_url(storage_path, 3600)["signedURL"]
