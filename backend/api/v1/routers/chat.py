from fastapi import APIRouter, Depends, Query, Request, status

from api.v1.models.chat_models import (
    CreateSessionRequest,
    MessageDeleteResponse,
    MessageResponse,
    RenameSessionRequest,
    SendMessageRequest,
    SessionResponse,
)
from auth.dependencies import get_current_user
from middleware.rate_limiter import limiter, AI_LIMIT
from services import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


# ─── Session Endpoints ──────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: CreateSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    return chat_service.create_session(current_user["user_id"], body.title)


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user)):
    return chat_service.list_sessions(current_user["user_id"])


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def rename_session(
    session_id: str,
    body: RenameSessionRequest,
    current_user: dict = Depends(get_current_user),
):
    return chat_service.rename_session(current_user["user_id"], session_id, body.title)


@router.delete("/sessions/{session_id}", response_model=MessageDeleteResponse)
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    return chat_service.delete_session(current_user["user_id"], session_id)


# ─── Message Endpoints ──────────────────────────────────────

@router.post("/{session_id}/messages", response_model=MessageResponse)
@limiter.limit(AI_LIMIT)
async def send_message(
    request: Request,
    session_id: str,
    body: SendMessageRequest,
    current_user: dict = Depends(get_current_user),
):
    return chat_service.send_message(current_user["user_id"], session_id, body.query)


@router.get("/{session_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    session_id: str,
    limit: int = Query(default=10, le=50),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    return chat_service.get_messages(current_user["user_id"], session_id, limit, offset)


@router.delete("/messages/{message_id}", response_model=MessageDeleteResponse)
async def delete_message(
    message_id: str,
    current_user: dict = Depends(get_current_user),
):
    return chat_service.delete_message(current_user["user_id"], message_id)
