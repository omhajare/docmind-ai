from pydantic import BaseModel


class EvalResultItem(BaseModel):
    question: str
    answer: str | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None


class SaveEvalResultsRequest(BaseModel):
    run_id: str
    eval_mode: str  # "rag_only" or "full_pipeline"
    results: list[EvalResultItem]


class SaveEvalResultsResponse(BaseModel):
    run_id: str
    eval_mode: str
    count: int


class EvalRunSummary(BaseModel):
    run_id: str
    eval_mode: str
    question_count: int
    avg_faithfulness: float
    avg_answer_relevancy: float
    avg_context_precision: float
    passed_count: int
    evaluated_at: str | None = None


class EvalResultDetail(BaseModel):
    id: str
    run_id: str
    eval_mode: str
    question: str
    answer: str | None = None
    faithfulness: float | None = None
    answer_relevancy: float | None = None
    context_precision: float | None = None
    passed: bool | None = None
    evaluated_at: str | None = None


class MessageResponse(BaseModel):
    message: str


class CleanupResponse(BaseModel):
    message: str
    sessions_deleted: int
