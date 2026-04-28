from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.responses import FileResponse

from api.v1.models.research_models import (
    JobStatusResponse,
    MessageResponse,
    StartResearchRequest,
    StartResearchResponse,
)
from auth.dependencies import get_current_user
from middleware.rate_limiter import limiter, AI_LIMIT
from services import research_service

router = APIRouter(prefix="/research", tags=["Research"])


# Route order matters: /history BEFORE /{job_id} routes

@router.post("", response_model=StartResearchResponse, status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(AI_LIMIT)
async def start_research(
    request: Request,
    body: StartResearchRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    result = research_service.start_job(current_user["user_id"], body.topic)
    background_tasks.add_task(
        research_service.run_research_agent,
        result["job_id"],
        body.topic.strip(),
        current_user["user_id"],
    )
    return result


@router.get("/history", response_model=list[JobStatusResponse])
async def get_history(current_user: dict = Depends(get_current_user)):
    return research_service.get_history(current_user["user_id"])


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    return research_service.get_job_status(current_user["user_id"], job_id)


@router.get("/{job_id}/download")
async def download_report(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    file_path = research_service.get_report_path(current_user["user_id"], job_id)
    filename = f"docmind_report_{job_id[:8]}.docx"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.delete("/{job_id}", response_model=MessageResponse)
async def cancel_job(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    return research_service.cancel_job(current_user["user_id"], job_id)
