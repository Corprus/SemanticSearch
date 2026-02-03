# app/routes/documents.py
from __future__ import annotations

from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Query
from pydantic import BaseModel

from services.document_service import DocumentService
from infrastructure.deps import get_document_service
from infrastructure.auth import authenticate, CurrentUser
from services import authorization

router = APIRouter()


class AddDocumentRequest(BaseModel):
    title: str
    content: str


class DocumentResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    content: str
    index_status: str


@router.put("", response_model=DocumentResponse, summary="Добавить документ пользователя")
def add_document(
    req: AddDocumentRequest, 
    docs: DocumentService = Depends(get_document_service),
    current_user: CurrentUser = Depends(authenticate)):
    user_id = authorization.resolve_target_user(current_user)
    doc = docs.add_document(user_id, req.title, req.content)
    return DocumentResponse(
        id=UUID(doc.id),
        owner_id=UUID(doc.owner_id),
        title=doc.title,
        content=doc.content,
        index_status=doc.index_status
    )

@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить документ пользователя из файла",
)
async def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    docs: DocumentService = Depends(get_document_service),
    current_user: CurrentUser = Depends(authenticate)):
    # Разрешаем только текстовые типы
    allowed = {"text/plain", "text/markdown", "application/json"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {sorted(allowed)}",
        )

    # Считываем файл
    raw = await file.read()

    # Лимит размера
    max_bytes = 2 * 1024 * 1024  # 2MB
    if len(raw) > max_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large (max 2MB)")

    # Превращаем в текст
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="File must be UTF-8 encoded text")

    user_id = authorization.resolve_target_user(current_user)
    # Прокидываем в севис
    doc = docs.add_document(user_id=user_id, title=title, content=content)

    return DocumentResponse(
        id=UUID(doc.id),
        owner_id=UUID(doc.owner_id),
        title=doc.title,
        content=doc.content,
        index_status=doc.index_status
    )


@router.get("/{document_id}", response_model=DocumentResponse, summary="Получить документ пользователя")
def get_document(
    document_id: UUID,
    user_id: UUID | None = Query(default=None),
    docs: DocumentService = Depends(get_document_service),
    current_user: CurrentUser = Depends(authenticate),
):
    user_id = authorization.resolve_target_user(current_user, user_id)
    doc = docs.get_user_document(user_id, document_id)
    return DocumentResponse(
        id=UUID(doc.id),
        owner_id=UUID(doc.owner_id),
        title=doc.title,
        content=doc.content,
        index_status=doc.index_status
    )


@router.get("", response_model=list[DocumentResponse], summary="Получить все документы пользователя")
def list_documents(user_id: UUID | None = Query(default=None), docs: DocumentService = Depends(get_document_service), current_user: CurrentUser = Depends(authenticate)):
    user_id = authorization.resolve_target_user(current_user, user_id)
    items = docs.list_documents(user_id)
    return [
        DocumentResponse(
            id=UUID(doc.id),
            owner_id=UUID(doc.owner_id),
            title=doc.title,
            content=doc.content,
            index_status=doc.index_status
        )
        for doc in items
    ]
