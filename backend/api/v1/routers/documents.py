from fastapi import APIRouter, Depends, UploadFile, File, status

from api.v1.models.document_models import (
    DeleteResponse,
    DocumentListResponse,
    SuggestedQuestionResponse,
    UploadResponse,
)
from auth.dependencies import get_current_user
from services import doc_service

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    return doc_service.upload_document(current_user["user_id"], file)


@router.get("", response_model=DocumentListResponse)
async def list_documents(current_user: dict = Depends(get_current_user)):
    return doc_service.list_documents(current_user["user_id"])


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    return doc_service.delete_document(current_user["user_id"], document_id)


@router.get("/{document_id}/suggested-questions", response_model=list[SuggestedQuestionResponse])
async def get_suggested_questions(
    document_id: str,
    current_user: dict = Depends(get_current_user),
):
    return doc_service.get_suggested_questions(document_id, current_user["user_id"])
