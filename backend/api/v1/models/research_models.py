from pydantic import BaseModel


class StartResearchRequest(BaseModel):
    topic: str


class StartResearchResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    topic: str
    status: str
    progress: dict | None = None
    confidence: str | None = None
    confidence_score: float | None = None
    report_path: str | None = None
    error_message: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class MessageResponse(BaseModel):
    message: str
