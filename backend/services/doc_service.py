import tempfile
import os

from fastapi import HTTPException, UploadFile, status
from langchain_google_genai import ChatGoogleGenerativeAI

from config import get_settings
from repositories import document_repository
from rag import indexer
from rag.retriever import delete_document_vectors
from utils.logger import logger

settings = get_settings()


def _get_storage():
    """Return the appropriate storage module based on environment."""
    if settings.is_production:
        from storage import supabase_storage as storage
    else:
        from storage import local_storage as storage
    return storage


def upload_document(user_id: str, file: UploadFile) -> dict:
    """Orchestrate document upload: validate → save → index → store metadata → generate questions."""
    # Validate MIME
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported",
        )

    # Read content and validate size
    content = file.file.read()
    file_size_kb = len(content) // 1024
    max_bytes = settings.MAX_PDF_SIZE_MB * 1024 * 1024

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.MAX_PDF_SIZE_MB} MB",
        )

    # Check document limit
    current_count = document_repository.count_by_user(user_id)
    if current_count >= settings.MAX_DOCUMENTS_PER_USER:
        existing = document_repository.find_by_user(user_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Document limit reached ({settings.MAX_DOCUMENTS_PER_USER})",
                "existing_documents": [
                    {"id": str(d["id"]), "filename": d["filename"]} for d in existing
                ],
            },
        )

    filename = file.filename or "document.pdf"
    storage = _get_storage()
    storage_path = None
    document_id = None

    try:
        # 1. Save file
        storage_path = storage.save_file(user_id, filename, content)

        # 2. Index: extract → chunk → embed → ChromaDB
        # Write to temp file for pdfplumber
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Generate a document ID first so we can use it in metadata
            import uuid
            document_id = str(uuid.uuid4())
            chunk_count = indexer.index_document(user_id, document_id, filename, tmp_path)
        finally:
            os.unlink(tmp_path)

        # 3. Store metadata in DB
        from database.db_client import get_db
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO documents (id, user_id, filename, storage_path, chunk_count, file_size_kb)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, user_id, filename, storage_path, chunk_count, file_size_kb, uploaded_at
                    """,
                    (document_id, user_id, filename, storage_path, chunk_count, file_size_kb),
                )
                document = dict(cur.fetchone())

        # 4. Generate suggested questions
        questions = generate_suggested_questions(document_id, user_id)

        logger.info(f"Document uploaded: {document_id} ({filename}, {chunk_count} chunks)")
        return {
            "document": _serialize_doc(document),
            "suggested_questions": questions,
        }

    except HTTPException:
        raise
    except Exception as e:
        # Rollback: delete file and vectors if they were created
        logger.error(f"Upload failed, rolling back: {e}")
        if storage_path:
            try:
                storage.delete_file(storage_path)
            except Exception:
                pass
        if document_id:
            try:
                delete_document_vectors(user_id, document_id)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document",
        )


def list_documents(user_id: str) -> dict:
    """List all documents for a user with count/limit info."""
    docs = document_repository.find_by_user(user_id)
    return {
        "documents": [_serialize_doc(d) for d in docs],
        "document_count": len(docs),
        "document_limit": settings.MAX_DOCUMENTS_PER_USER,
    }


def delete_document(user_id: str, document_id: str) -> dict:
    """Delete a document from all layers. Continue on partial failure."""
    doc = document_repository.find_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if str(doc["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    warnings = []
    storage = _get_storage()

    # 1. Delete file from storage
    try:
        storage.delete_file(doc["storage_path"])
    except Exception as e:
        logger.error(f"Failed to delete file: {e}")
        warnings.append(f"Failed to delete file from storage: {str(e)}")

    # 2. Delete vectors from ChromaDB
    try:
        delete_document_vectors(user_id, document_id)
    except Exception as e:
        logger.error(f"Failed to delete vectors: {e}")
        warnings.append(f"Failed to delete vectors from ChromaDB: {str(e)}")

    # 3. Delete DB record (cascades to suggested_questions)
    try:
        document_repository.delete(document_id)
    except Exception as e:
        logger.error(f"Failed to delete DB record: {e}")
        warnings.append(f"Failed to delete database record: {str(e)}")

    result = {"success": True, "message": "Document deleted"}
    if warnings:
        result["warnings"] = warnings

    logger.info(f"Document deleted: {document_id}")
    return result


def get_suggested_questions(document_id: str, user_id: str) -> list[dict]:
    """Get suggested questions (cached or generate new)."""
    doc = document_repository.find_by_id(document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    if str(doc["user_id"]) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    cached = document_repository.get_suggested_questions(document_id)
    if cached:
        return [{"id": str(q["id"]), "question": q["question"]} for q in cached]

    return generate_suggested_questions(document_id, user_id)


def generate_suggested_questions(document_id: str, user_id: str) -> list[dict]:
    """Generate questions using the LLM and cache them."""
    from rag.retriever import get_collection_name, get_chroma_client

    collection_name = get_collection_name(user_id)
    client = get_chroma_client()

    try:
        collection = client.get_collection(name=collection_name)
        results = collection.get(
            where={"document_id": document_id},
            limit=3,
            include=["documents"],
        )
        chunks = results.get("documents", [])
        if not chunks:
            return []
        context = "\n\n".join(chunks[:3])
    except Exception:
        return []

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
        )
        prompt = f"""Based on the following document content, generate exactly {settings.SUGGESTED_QUESTIONS_COUNT} 
thoughtful, specific questions that a reader might want to ask about this document. 
Return ONLY the questions, one per line, without numbering or bullet points.

<document_content>
{context}
</document_content>"""

        response = llm.invoke(prompt)
        questions = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
        questions = questions[:settings.SUGGESTED_QUESTIONS_COUNT]
    except Exception as e:
        logger.error(f"Failed to generate questions: {e}")
        return []

    saved = document_repository.save_suggested_questions(document_id, user_id, questions)
    return [{"id": str(q["id"]), "question": q["question"]} for q in saved]


def _serialize_doc(doc: dict) -> dict:
    return {
        "id": str(doc["id"]),
        "filename": doc["filename"],
        "storage_path": doc["storage_path"],
        "chunk_count": doc["chunk_count"],
        "file_size_kb": doc.get("file_size_kb"),
        "uploaded_at": doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None,
    }
