from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    title: str | None = None


class RenameSessionRequest(BaseModel):
    title: str


class SendMessageRequest(BaseModel):
    query: str


class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None


class SourceInfo(BaseModel):
    document_sources: list[dict] = []
    web_sources: list[dict] = []


class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: SourceInfo | dict | None = None
    tools_used: list[str] | None = None
    confidence: str | None = None
    created_at: str | None = None


class MessageDeleteResponse(BaseModel):
    message: str
