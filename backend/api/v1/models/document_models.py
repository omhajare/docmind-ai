from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    storage_path: str
    chunk_count: int
    file_size_kb: int | None = None
    uploaded_at: str | None = None


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    document_count: int
    document_limit: int


class SuggestedQuestionResponse(BaseModel):
    id: str
    question: str


class UploadResponse(BaseModel):
    document: DocumentResponse
    suggested_questions: list[SuggestedQuestionResponse]


class DeleteResponse(BaseModel):
    success: bool
    message: str
    warnings: list[str] | None = None
