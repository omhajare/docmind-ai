import uuid

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import get_settings
from rag.retriever import get_collection_name, get_chroma_client
from utils.logger import logger

settings = get_settings()


def _get_embeddings_model() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=settings.GEMINI_API_KEY,
    )


def extract_text_from_pdf(file_path: str) -> list[dict]:
    """Extract text from each page of a PDF. Returns [{ page: int, text: str }]."""
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i + 1, "text": text.strip()})
    return pages


def chunk_text(pages: list[dict], chunk_size: int | None = None, chunk_overlap: int | None = None) -> list[dict]:
    """Split page text into overlapping chunks with metadata."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )

    chunks = []
    chunk_index = 0
    for page_data in pages:
        page_chunks = splitter.split_text(page_data["text"])
        for text in page_chunks:
            chunks.append({
                "text": text,
                "page_number": page_data["page"],
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    return chunks


def index_document(
    user_id: str,
    document_id: str,
    filename: str,
    file_path: str,
) -> int:
    """Full indexing pipeline: extract → chunk → embed → store in ChromaDB.
    Returns the number of chunks indexed.
    """
    # 1. Extract text
    pages = extract_text_from_pdf(file_path)
    if not pages:
        logger.warning(f"No text extracted from {filename}")
        return 0

    # 2. Chunk
    chunks = chunk_text(pages)
    if not chunks:
        return 0

    logger.info(f"Indexing {len(chunks)} chunks for {filename}")

    # 3. Embed
    embeddings_model = _get_embeddings_model()
    texts = [c["text"] for c in chunks]
    embeddings = embeddings_model.embed_documents(texts)

    # 4. Store in ChromaDB
    collection_name = get_collection_name(user_id)
    client = get_chroma_client()
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "page_number": c["page_number"],
            "chunk_index": c["chunk_index"],
            "user_id": user_id,
        }
        for c in chunks
    ]

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    logger.info(f"Indexed {len(chunks)} chunks into {collection_name}")
    return len(chunks)


def get_embedding(text: str) -> list[float]:
    """Generate embedding for a single query text."""
    model = _get_embeddings_model()
    return model.embed_query(text)
